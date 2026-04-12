from pydantic import BaseModel, Field


class DevLoginRequest(BaseModel):
    telegram_user_id: int = Field(..., ge=1)
    is_coach: bool = False
    full_name: str | None = None


class TelegramInitRequest(BaseModel):
    init_data: str = Field(..., min_length=1)


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenPairResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
