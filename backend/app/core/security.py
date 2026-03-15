from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException, status
from fastapi.security import HTTPBearer
from jose import JWTError, jwt

from app.core.config import settings

bearer_scheme = HTTPBearer(auto_error=False)

ALGORITHM = "HS256"
_REFRESH_TOKEN_TYPE = "refresh"


def create_access_token(data: dict[str, Any]) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({**data, "exp": expire}, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict[str, Any]) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return jwt.encode(
        {**data, "exp": expire, "type": _REFRESH_TOKEN_TYPE},
        settings.SECRET_KEY,
        algorithm=ALGORITHM,
    )


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


def decode_refresh_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != _REFRESH_TOKEN_TYPE:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
