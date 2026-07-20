from pydantic import BaseModel, Field


class DevLoginRequest(BaseModel):
    telegram_user_id: int = Field(..., ge=1)
    is_coach: bool = False
    is_admin: bool = False
    username: str | None = Field(default=None, max_length=64)
    full_name: str | None = Field(default=None, max_length=128)


class TelegramInitRequest(BaseModel):
    init_data: str = Field(..., min_length=1)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1, max_length=4096)


class TokenPairResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
