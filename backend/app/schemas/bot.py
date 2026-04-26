from pydantic import BaseModel, Field


class BotTimezoneUpdateRequest(BaseModel):
    telegram_user_id: int = Field(..., ge=1)
    timezone: str = Field(..., min_length=1, max_length=64)
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None


class BotTimezoneUpdateResponse(BaseModel):
    telegram_user_id: int
    timezone: str
