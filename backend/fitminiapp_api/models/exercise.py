from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from fitminiapp_api.db.base import Base


class Exercise(Base):
    __tablename__ = "exercises"
    __table_args__ = (
        CheckConstraint(
            "difficulty_level IN ('beginner', 'intermediate', 'advanced')",
            name="ck_exercises_difficulty_level",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    primary_muscle: Mapped[str | None] = mapped_column(String(64), nullable=True)
    equipment: Mapped[str | None] = mapped_column(String(64), nullable=True)
    difficulty_level: Mapped[str] = mapped_column(
        String(16), nullable=False, default="intermediate", server_default="intermediate"
    )

    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    source_exercise_id: Mapped[int | None] = mapped_column(
        ForeignKey("exercises.id"),
        nullable=True,
        index=True,
    )

    is_deleted: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
