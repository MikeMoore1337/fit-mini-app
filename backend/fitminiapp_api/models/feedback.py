from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from fitminiapp_api.core.timezone import now_msk_naive
from fitminiapp_api.db.base import Base


class WorkoutComment(Base):
    __tablename__ = "workout_comments"
    __table_args__ = (
        CheckConstraint(
            "length(body) BETWEEN 1 AND 2000",
            name="ck_workout_comments_body_length",
        ),
        Index(
            "ix_workout_comments_client_workout_created",
            "client_user_id",
            "workout_id",
            "created_at",
            "id",
        ),
        Index(
            "ix_workout_comments_relation_workout_created",
            "coach_client_id",
            "workout_id",
            "created_at",
            "id",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    coach_client_id: Mapped[int] = mapped_column(
        ForeignKey("coach_clients.id", ondelete="CASCADE"), nullable=False
    )
    trainer_author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    client_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    workout_id: Mapped[int] = mapped_column(
        ForeignKey("user_workouts.id", ondelete="CASCADE"), nullable=False
    )
    workout_exercise_id: Mapped[int | None] = mapped_column(
        ForeignKey("user_workout_exercises.id", ondelete="SET NULL"), nullable=True
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=now_msk_naive)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    revisions: Mapped[list[WorkoutCommentRevision]] = relationship(
        "WorkoutCommentRevision",
        back_populates="comment",
        cascade="all, delete-orphan",
        order_by="WorkoutCommentRevision.revision_number",
    )


class WorkoutCommentRevision(Base):
    __tablename__ = "workout_comment_revisions"
    __table_args__ = (
        UniqueConstraint(
            "comment_id",
            "revision_number",
            name="uq_workout_comment_revisions_comment_number",
        ),
        CheckConstraint(
            "length(body) BETWEEN 1 AND 2000",
            name="ck_workout_comment_revisions_body_length",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    comment_id: Mapped[int] = mapped_column(
        ForeignKey("workout_comments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    revision_number: Mapped[int] = mapped_column(Integer, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    edited_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=now_msk_naive)

    comment: Mapped[WorkoutComment] = relationship("WorkoutComment", back_populates="revisions")
