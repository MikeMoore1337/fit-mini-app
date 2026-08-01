from pydantic import BaseModel


class TelegramInitRequest(BaseModel):
    init_data: str


class TokenPairResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
