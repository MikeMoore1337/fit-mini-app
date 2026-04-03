from pydantic import BaseModel


class TelegramInitRequest(BaseModel):
    init_data: str


class DevLoginRequest(BaseModel):
    telegram_user_id: int
    full_name: str | None = None
    is_coach: bool = False


class TokenPairResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
