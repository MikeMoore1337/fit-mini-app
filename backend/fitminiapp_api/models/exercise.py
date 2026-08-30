from __future__ import annotations

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

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
    metric_type: Mapped[str | None] = mapped_column(String(16), nullable=True)
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

    muscle_links: Mapped[list[ExerciseMuscle]] = relationship(
        back_populates="exercise",
        cascade="all, delete-orphan",
        order_by="ExerciseMuscle.role, ExerciseMuscle.position",
    )
    equipment_links: Mapped[list[ExerciseEquipment]] = relationship(
        back_populates="exercise",
        cascade="all, delete-orphan",
        order_by="ExerciseEquipment.position",
    )
    guide_metadata: Mapped[ExerciseGuideMetadata | None] = relationship(
        back_populates="exercise",
        cascade="all, delete-orphan",
        uselist=False,
    )


class Muscle(Base):
    __tablename__ = "muscles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    identifier: Mapped[str] = mapped_column(String(48), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)


class Equipment(Base):
    __tablename__ = "equipment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    identifier: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)


class ExerciseMuscle(Base):
    __tablename__ = "exercise_muscles"
    __table_args__ = (
        UniqueConstraint(
            "exercise_id",
            "role",
            "position",
            name="uq_exercise_muscles_role_position",
        ),
        CheckConstraint(
            "role IN ('primary', 'secondary')",
            name="ck_exercise_muscles_role",
        ),
        CheckConstraint("position >= 0", name="ck_exercise_muscles_position"),
        Index("ix_exercise_muscles_muscle_role_exercise", "muscle_id", "role", "exercise_id"),
    )

    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercises.id", ondelete="CASCADE"),
        primary_key=True,
    )
    muscle_id: Mapped[int] = mapped_column(
        ForeignKey("muscles.id", ondelete="RESTRICT"),
        primary_key=True,
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    exercise: Mapped[Exercise] = relationship(back_populates="muscle_links")
    muscle: Mapped[Muscle] = relationship()


class ExerciseEquipment(Base):
    __tablename__ = "exercise_equipment"
    __table_args__ = (
        UniqueConstraint(
            "exercise_id",
            "position",
            name="uq_exercise_equipment_position",
        ),
        CheckConstraint("position >= 0", name="ck_exercise_equipment_position"),
        Index("ix_exercise_equipment_equipment_exercise", "equipment_id", "exercise_id"),
    )

    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercises.id", ondelete="CASCADE"),
        primary_key=True,
    )
    equipment_id: Mapped[int] = mapped_column(
        ForeignKey("equipment.id", ondelete="RESTRICT"),
        primary_key=True,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    exercise: Mapped[Exercise] = relationship(back_populates="equipment_links")
    equipment: Mapped[Equipment] = relationship()


class ExerciseAlternative(Base):
    __tablename__ = "exercise_alternatives"
    __table_args__ = (
        CheckConstraint(
            "exercise_id < alternative_exercise_id",
            name="ck_exercise_alternatives_ordered_pair",
        ),
        Index(
            "ix_exercise_alternatives_reverse",
            "alternative_exercise_id",
            "exercise_id",
        ),
    )

    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercises.id", ondelete="CASCADE"),
        primary_key=True,
    )
    alternative_exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercises.id", ondelete="CASCADE"),
        primary_key=True,
    )


class ExerciseGuideMetadata(Base):
    __tablename__ = "exercise_guide_metadata"

    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercises.id", ondelete="CASCADE"),
        primary_key=True,
    )
    safety_notes: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        server_default="[]",
    )
    source_name: Mapped[str] = mapped_column(String(128), nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    source_license: Mapped[str] = mapped_column(String(128), nullable=False)
    source_license_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    media_reference: Mapped[str] = mapped_column(String(128), nullable=False)

    exercise: Mapped[Exercise] = relationship(back_populates="guide_metadata")
