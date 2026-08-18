from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

COMMENT_MAX_LENGTH = 2000


def _normalize_plain_text(value: str) -> str:
    normalized = value.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        raise ValueError("Комментарий не может быть пустым")
    if any(ord(character) < 32 and character not in {"\n", "\t"} for character in normalized):
        raise ValueError("Комментарий содержит недопустимые управляющие символы")
    return normalized


class WorkoutCommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=COMMENT_MAX_LENGTH)
    workout_exercise_id: int | None = Field(default=None, gt=0)

    @field_validator("body")
    @classmethod
    def validate_body(cls, value: str) -> str:
        return _normalize_plain_text(value)


class WorkoutCommentUpdate(BaseModel):
    body: str = Field(min_length=1, max_length=COMMENT_MAX_LENGTH)

    @field_validator("body")
    @classmethod
    def validate_body(cls, value: str) -> str:
        return _normalize_plain_text(value)


class WorkoutCommentRevisionResponse(BaseModel):
    id: int
    revision_number: int
    body: str
    edited_by_user_id: int
    created_at: datetime


class WorkoutCommentResponse(BaseModel):
    id: int
    trainer_author_id: int
    client_user_id: int
    workout_id: int
    workout_exercise_id: int | None = None
    body: str
    body_format: Literal["plain_text"] = "plain_text"
    created_at: datetime
    updated_at: datetime | None = None
    revisions: list[WorkoutCommentRevisionResponse] = Field(default_factory=list)
