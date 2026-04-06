from app.db.base import Base
from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column


class Exercise(Base):
    __tablename__ = "exercises"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    primary_muscle: Mapped[str] = mapped_column(String(64), nullable=False)
    equipment: Mapped[str] = mapped_column(String(64), nullable=False)

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
