import re

from pydantic import BaseModel, Field, field_validator


class DevLoginRequest(BaseModel):
    telegram_user_id: int = Field(..., ge=1)
    is_coach: bool = False
    is_admin: bool = False
    username: str | None = Field(default=None, max_length=64)
    full_name: str | None = Field(default=None, max_length=128)


class TelegramInitRequest(BaseModel):
    init_data: str = Field(..., min_length=1, max_length=16_384)


class RefreshRequest(BaseModel):
    refresh_token: str | None = Field(default=None, min_length=1, max_length=4096)


class TokenPairResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


USERNAME_PATTERN = re.compile(r"[a-z0-9][a-z0-9_.-]{2,31}\Z")
EMAIL_PATTERN = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+\Z")


def normalize_email(value: str) -> str:
    normalized = value.strip().lower()
    if len(normalized) > 320 or not EMAIL_PATTERN.fullmatch(normalized):
        raise ValueError("Некорректный email")
    return normalized


def normalize_local_username(value: str) -> str:
    normalized = value.strip().lower()
    if not USERNAME_PATTERN.fullmatch(normalized):
        raise ValueError(
            "Имя пользователя: 3–32 символа, латинские буквы, цифры, точка, дефис или подчёркивание"
        )
    return normalized


def normalize_next_path(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    normalized = value.strip()
    if not re.fullmatch(r"/join/[A-Za-z0-9_-]{20,128}", normalized):
        raise ValueError("Некорректный адрес возврата")
    return normalized


class EmailRegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    email: str = Field(min_length=5, max_length=320)
    password: str = Field(min_length=12, max_length=128)
    next_path: str | None = Field(default=None, max_length=160)

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        return normalize_local_username(value)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return normalize_email(value)

    @field_validator("next_path")
    @classmethod
    def validate_next_path(cls, value: str | None) -> str | None:
        return normalize_next_path(value)


class EmailLoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=320)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return normalize_email(value)


class AuthTokenRequest(BaseModel):
    token: str = Field(min_length=32, max_length=256, pattern=r"^[A-Za-z0-9_-]+$")


class EmailRequest(BaseModel):
    email: str = Field(min_length=5, max_length=320)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return normalize_email(value)


class PasswordResetConfirmRequest(AuthTokenRequest):
    password: str = Field(min_length=12, max_length=128)


class RegistrationResponse(BaseModel):
    verification_required: bool = True
    verification_token: str | None = None


class MessageResponse(BaseModel):
    message: str
    action_token: str | None = None
