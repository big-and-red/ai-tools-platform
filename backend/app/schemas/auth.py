from pydantic import BaseModel


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    credits_balance: int


class GoogleCallbackQuery(BaseModel):
    code: str
    state: str | None = None
