import secrets
from urllib.parse import urlencode
from uuid import UUID

import httpx
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.containers import Container
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)
from app.repositories.user import UserRepository

router = APIRouter(prefix="/auth", tags=["auth"])

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
SCOPES = "openid email profile"

_OAUTH_STATE_TTL = 300  # 5 minutes
_REFRESH_COOKIE = "refresh_token"


@router.get("/google")
@inject
async def google_login(
    redis=Depends(Provide[Container.redis_client]),
) -> RedirectResponse:
    """Redirect user to Google OAuth consent screen (CSRF state included)."""
    state = secrets.token_urlsafe(32)
    await redis.setex(f"oauth_state:{state}", _OAUTH_STATE_TTL, "1")

    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPES,
        "access_type": "offline",
        "state": state,
    }
    return RedirectResponse(f"{GOOGLE_AUTH_URL}?{urlencode(params)}")


@router.get("/google/callback")
@inject
async def google_callback(
    code: str,
    state: str | None = None,
    session: AsyncSession = Depends(get_db),
    redis=Depends(Provide[Container.redis_client]),
) -> RedirectResponse:
    """Exchange Google code for user info, create/find user, issue JWT pair."""
    # CSRF validation
    if not state or not await redis.get(f"oauth_state:{state}"):
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")
    await redis.delete(f"oauth_state:{state}")

    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )
        if token_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Google token exchange failed")
        google_token = token_resp.json()["access_token"]

        user_resp = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {google_token}"},
        )
        if user_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch Google user info")
        google_user = user_resp.json()

    google_id: str = google_user["sub"]
    email: str = google_user["email"]

    repo = UserRepository()
    user = await repo.get_by_google_id(session, google_id)
    if not user:
        user = await repo.get_by_email(session, email)
        if user:
            user.google_id = google_id
        else:
            user = await repo.create_oauth_user(session, email=email, google_id=google_id)
    await session.commit()

    token_data = {"sub": str(user.id), "email": user.email}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    # Pass access_token via hash fragment (not logged by proxies, not in browser history)
    response = RedirectResponse(
        f"{settings.FRONTEND_URL}/auth/callback#token={access_token}"
    )
    response.set_cookie(
        key=_REFRESH_COOKIE,
        value=refresh_token,
        httponly=True,
        secure=settings.FRONTEND_URL.startswith("https"),
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        path="/api/v1/auth/refresh",
    )
    return response


@router.post("/refresh")
async def refresh_token(
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Issue a new access token using the httpOnly refresh token cookie."""
    token = request.cookies.get(_REFRESH_COOKIE)
    if not token:
        raise HTTPException(status_code=401, detail="No refresh token")

    payload = decode_refresh_token(token)
    user_id = UUID(payload["sub"])

    repo = UserRepository()
    user = await repo.get_by_id(session, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    access_token = create_access_token({"sub": str(user.id), "email": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
async def logout() -> dict[str, str]:
    """Clear the refresh token cookie."""
    from fastapi.responses import JSONResponse
    response = JSONResponse(content={"detail": "Logged out"})
    response.delete_cookie(key=_REFRESH_COOKIE, path="/api/v1/auth/refresh")
    return response  # type: ignore[return-value]


@router.get("/me")
async def get_me(
    user_id: UUID = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> dict[str, str | int]:
    repo = UserRepository()
    user = await repo.get_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "user_id": str(user.id),
        "email": user.email,
        "credits_balance": user.credits_balance,
    }
