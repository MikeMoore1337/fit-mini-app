from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from fitminiapp_api.core.timezone import now_msk_naive
from fitminiapp_api.db.base import Base
from fitminiapp_api.models.exercise import Exercise


class ProgramTemplate(Base):
    __tablename__ = "program_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(128))
    goal: Mapped[str] = mapped_column(String(32))
    level: Mapped[str] = mapped_column(String(32))
    owner_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), index=True, nullable=True
    )
    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), index=True, nullable=True
    )
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=now_msk_naive,
        server_default=func.now(),
    )

    days: Mapped[list[ProgramTemplateDay]] = relationship(
        "ProgramTemplateDay",
        back_populates="program",
        cascade="all, delete-orphan",
        order_by="ProgramTemplateDay.day_number",
    )


class HiddenProgramTemplate(Base):
    """A system example hidden from one user's personal library."""

    __tablename__ = "hidden_program_templates"
    __table_args__ = (
        UniqueConstraint("user_id", "template_id", name="uq_hidden_program_template"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    template_id: Mapped[int] = mapped_column(
        ForeignKey("program_templates.id"), nullable=False, index=True
    )
    hidden_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=now_msk_naive,
        server_default=func.now(),
    )


class ProgramTemplateDay(Base):
    __tablename__ = "program_template_days"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    program_id: Mapped[int] = mapped_column(ForeignKey("program_templates.id"), index=True)
    day_number: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(128))

    program: Mapped[ProgramTemplate] = relationship("ProgramTemplate", back_populates="days")
    exercises: Mapped[list[ProgramTemplateExercise]] = relationship(
        "ProgramTemplateExercise",
        back_populates="day",
        cascade="all, delete-orphan",
        order_by="ProgramTemplateExercise.sort_order",
    )


class ProgramTemplateExercise(Base):
    __tablename__ = "program_template_exercises"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    day_id: Mapped[int] = mapped_column(ForeignKey("program_template_days.id"), index=True)
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercises.id"), index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=1)
    prescribed_sets: Mapped[int] = mapped_column(Integer)
    prescribed_reps: Mapped[str] = mapped_column(String(32))
    rest_seconds: Mapped[int] = mapped_column(Integer, default=90)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    day: Mapped[ProgramTemplateDay] = relationship("ProgramTemplateDay", back_populates="exercises")
    exercise: Mapped[Exercise] = relationship("Exercise")


class UserProgram(Base):
    __tablename__ = "user_programs"
    __table_args__ = (
        Index(
            "uq_user_programs_one_active_per_user",
            "user_id",
            unique=True,
            postgresql_where=text("is_active"),
            sqlite_where=text("is_active = 1"),
        ),
        CheckConstraint(
            "status IN ('scheduled', 'active', 'completed', 'archived')",
            name="ck_user_programs_status",
        ),
        CheckConstraint("duration_weeks >= 1", name="ck_user_programs_duration_weeks"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    # Назначение и история должны переживать архивирование исходного шаблона.
    template_id: Mapped[int | None] = mapped_column(
        ForeignKey("program_templates.id"), index=True, nullable=True
    )
    assigned_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), index=True, nullable=True
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=now_msk_naive,
        server_default=func.now(),
    )
    start_date: Mapped[date] = mapped_column(
        Date, nullable=False, default=date.today, server_default=func.current_date()
    )
    duration_weeks: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default="1"
    )
    schedule_weekdays: Mapped[list[int]] = mapped_column(
        JSON, nullable=False, default=list, server_default="[]"
    )
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="active", server_default="active"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    template: Mapped[ProgramTemplate | None] = relationship("ProgramTemplate")
    workouts: Mapped[list[UserWorkout]] = relationship(
        "UserWorkout", back_populates="user_program", cascade="all, delete-orphan"
    )


class UserWorkout(Base):
    __tablename__ = "user_workouts"
    __table_args__ = (
        Index(
            "ix_user_workouts_program_date_status",
            "user_program_id",
            "scheduled_date",
            "status",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_program_id: Mapped[int] = mapped_column(ForeignKey("user_programs.id"), index=True)
    scheduled_date: Mapped[date] = mapped_column(Date, index=True)
    day_number: Mapped[int] = mapped_column(Integer)
    week_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    title: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32), default="planned")
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user_program: Mapped[UserProgram] = relationship("UserProgram", back_populates="workouts")
    exercises: Mapped[list[UserWorkoutExercise]] = relationship(
        "UserWorkoutExercise",
        back_populates="workout",
        cascade="all, delete-orphan",
        order_by="UserWorkoutExercise.sort_order",
    )


class UserWorkoutExercise(Base):
    __tablename__ = "user_workout_exercises"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workout_id: Mapped[int] = mapped_column(ForeignKey("user_workouts.id"), index=True)
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercises.id"), index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=1)
    prescribed_sets: Mapped[int] = mapped_column(Integer)
    prescribed_reps: Mapped[str] = mapped_column(String(32))
    rest_seconds: Mapped[int] = mapped_column(Integer, default=90)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    workout: Mapped[UserWorkout] = relationship("UserWorkout", back_populates="exercises")
    exercise: Mapped[Exercise] = relationship("Exercise")
    sets: Mapped[list[UserWorkoutSet]] = relationship(
        "UserWorkoutSet",
        back_populates="workout_exercise",
        cascade="all, delete-orphan",
        order_by="UserWorkoutSet.set_number",
    )


class UserWorkoutSet(Base):
    __tablename__ = "user_workout_sets"
    __table_args__ = (
        UniqueConstraint(
            "workout_exercise_id",
            "set_number",
            name="uq_user_workout_sets_exercise_number",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workout_exercise_id: Mapped[int] = mapped_column(
        ForeignKey("user_workout_exercises.id"), index=True
    )
    set_number: Mapped[int] = mapped_column(Integer)
    actual_reps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actual_weight: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)

    workout_exercise: Mapped[UserWorkoutExercise] = relationship(
        "UserWorkoutExercise", back_populates="sets"
    )
