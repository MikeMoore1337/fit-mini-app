from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError
from sqlalchemy.orm import Session

from fitminiapp_api.models.food import Food
from fitminiapp_api.schemas.food import FoodCatalog


class FoodImportError(ValueError):
    pass


@dataclass(frozen=True)
class FoodImportResult:
    created: int
    updated: int


def load_food_catalog(path: Path) -> FoodCatalog:
    try:
        raw_catalog = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FoodImportError(f"cannot read food catalog: {exc}") from exc
    try:
        return FoodCatalog.model_validate(raw_catalog)
    except ValidationError as exc:
        raise FoodImportError(f"invalid food catalog: {exc}") from exc


def import_food_catalog(db: Session, catalog: FoodCatalog) -> FoodImportResult:
    source = catalog.source
    source_name = source.name
    external_ids = [item.external_id for item in catalog.foods]
    existing_by_external_id = {
        food.external_id: food
        for food in db.query(Food)
        .filter(
            Food.provenance == "external",
            Food.source_name == source_name,
            Food.external_id.in_(external_ids),
        )
        .all()
    }
    created = 0
    updated = 0

    for item in catalog.foods:
        food = existing_by_external_id.get(item.external_id)
        if food is None:
            food = Food()
            db.add(food)
            created += 1
        else:
            updated += 1

        values = item.model_dump()
        for field, value in values.items():
            setattr(food, field, value)
        food.owner_user_id = None
        food.provenance = "external"
        food.source_name = source_name
        food.source_version = source.version
        food.source_license = source.license
        food.source_url = str(source.source_url)
        food.source_license_url = str(source.license_url)
        food.trust_level = "verified"

    db.flush()
    return FoodImportResult(created=created, updated=updated)
