from uuid import UUID

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    status_code: int = 500
    detail: str = "Internal server error"


class NotFoundError(AppError):
    status_code = 404

    def __init__(self, entity: str, id: UUID | str) -> None:
        self.detail = f"{entity} '{id}' not found"


class InsufficientCreditsError(AppError):
    status_code = 402

    def __init__(self, required: int, available: int) -> None:
        self.detail = f"Insufficient credits: required {required}, available {available}"


class UnauthorizedError(AppError):
    status_code = 401
    detail = "Unauthorized"


def friendly_error(exc: Exception) -> str:
    """Map provider/infra exceptions to user-facing messages."""
    msg = str(exc)
    if "unsupported_country_region_territory" in msg:
        return "AI provider is not available in your region. Please use a VPN."
    if "rate_limit" in msg or "RateLimitError" in type(exc).__name__:
        return "AI provider rate limit reached. Please try again in a few minutes."
    if "AuthenticationError" in type(exc).__name__ or "invalid_api_key" in msg:
        return "AI provider authentication failed. Please contact support."
    if "Connection" in type(exc).__name__ or "timeout" in msg.lower():
        return "Connection to AI provider timed out. Please try again."
    if "tavily" in msg.lower():
        return "Search service is temporarily unavailable. Please try again."
    return f"Agent error: {msg}"


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )
