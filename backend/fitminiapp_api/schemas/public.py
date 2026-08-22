from typing import Literal

from pydantic import BaseModel


class PublicExerciseSummary(BaseModel):
    slug: str
    title: str
    primary_muscle: str
    secondary_muscles: list[str]
    equipment: str
    difficulty_level: Literal["beginner", "intermediate", "advanced"]


class PublicExerciseDetail(PublicExerciseSummary):
    technique_steps: list[str]
    breathing: str
    common_mistakes: list[str]
    safety_notes: list[str]
    source_name: str
    source_url: str
    source_license: str
    source_license_url: str | None = None
