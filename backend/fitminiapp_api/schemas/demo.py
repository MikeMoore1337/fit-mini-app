from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator

DemoScenario = Literal["self_training", "nutrition", "trainer"]


class DemoExercise(BaseModel):
    name: str
    prescription: str
    status: Literal["completed", "current", "next"]


class DemoSelfTrainingState(BaseModel):
    kind: Literal["self_training"] = "self_training"
    screen: Literal["today", "active_workout", "summary", "progress"]
    workout_title: str
    workout_subtitle: str
    completed_sets: int = Field(ge=0)
    total_sets: int = Field(ge=1)
    exercises: list[DemoExercise]
    duration_minutes: int = Field(ge=0)
    total_volume_kg: int = Field(ge=0)
    progress_change_percent: float


class DemoNutritionItem(BaseModel):
    name: str
    serving: str
    calories: int = Field(ge=0)
    protein_g: float = Field(ge=0)


class DemoNutritionState(BaseModel):
    kind: Literal["nutrition"] = "nutrition"
    screen: Literal["diary", "report"]
    date_label: str
    item_added: bool
    recent_item: DemoNutritionItem
    calories: int = Field(ge=0)
    calorie_target: int = Field(gt=0)
    protein_g: float = Field(ge=0)
    protein_target_g: float = Field(gt=0)
    meals_logged: int = Field(ge=0)


class DemoTrainerFact(BaseModel):
    label: str
    value: str


class DemoTrainerState(BaseModel):
    kind: Literal["trainer"] = "trainer"
    screen: Literal["client"] = "client"
    client_name: str
    context_label: str
    workout_title: str
    facts: list[DemoTrainerFact]
    comment: str | None = None


DemoScenarioState = Annotated[
    DemoSelfTrainingState | DemoNutritionState | DemoTrainerState,
    Field(discriminator="kind"),
]


class DemoSessionCreateRequest(BaseModel):
    scenario: DemoScenario


class DemoActionRequest(BaseModel):
    action: str = Field(min_length=1, max_length=64, pattern=r"^[a-z][a-z0-9_]*$")
    comment: str | None = Field(default=None, max_length=280)

    @field_validator("comment")
    @classmethod
    def normalize_comment(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = " ".join(value.split())
        if not normalized:
            raise ValueError("Комментарий не может быть пустым")
        return normalized


class DemoSessionSnapshot(BaseModel):
    capability: Literal["demo"] = "demo"
    scenario: DemoScenario
    fixture_version: Literal["demo-curated-v1"] = "demo-curated-v1"
    revision: int = Field(ge=1)
    expires_at: datetime
    state: DemoScenarioState


class DemoSessionCreated(DemoSessionSnapshot):
    session_token: str
