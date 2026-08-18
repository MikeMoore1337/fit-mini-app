from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal, Protocol

from pydantic import ValidationError

from fitminiapp_api.core.config import settings
from fitminiapp_api.schemas.food import ExternalFoodResponse, ExternalFoodSource, ServingUnit

FoodProviderFailureReason = Literal[
    "timeout",
    "network_error",
    "rate_limited",
    "upstream_error",
    "malformed_response",
]


class FoodProviderUnavailable(RuntimeError):
    def __init__(self, reason: FoodProviderFailureReason) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True)
class ProviderFood:
    external_id: str
    name: str
    brand: str | None
    barcode: str
    energy_kcal_per_100g: Decimal
    protein_g_per_100g: Decimal
    fat_g_per_100g: Decimal
    carbs_g_per_100g: Decimal
    fiber_g_per_100g: Decimal | None
    standard_serving_amount: Decimal | None
    standard_serving_unit: ServingUnit | None
    standard_serving_weight_g: Decimal | None
    provider: str
    attribution: str
    source_url: str
    license: str
    license_url: str


class FoodProvider(Protocol):
    def search(self, query: str, *, limit: int) -> list[ProviderFood]: ...

    def get_by_barcode(self, barcode: str) -> ProviderFood | None: ...


def serialize_provider_food(food: ProviderFood) -> ExternalFoodResponse:
    try:
        return ExternalFoodResponse(
            external_id=food.external_id,
            name=food.name,
            brand=food.brand,
            barcode=food.barcode,
            energy_kcal_per_100g=food.energy_kcal_per_100g,
            protein_g_per_100g=food.protein_g_per_100g,
            fat_g_per_100g=food.fat_g_per_100g,
            carbs_g_per_100g=food.carbs_g_per_100g,
            fiber_g_per_100g=food.fiber_g_per_100g,
            standard_serving_amount=food.standard_serving_amount,
            standard_serving_unit=food.standard_serving_unit,
            standard_serving_weight_g=food.standard_serving_weight_g,
            source=ExternalFoodSource.model_validate(
                {
                    "provider": food.provider,
                    "attribution": food.attribution,
                    "source_url": food.source_url,
                    "license": food.license,
                    "license_url": food.license_url,
                }
            ),
        )
    except ValidationError as exc:
        raise FoodProviderUnavailable("malformed_response") from exc


def get_food_provider() -> FoodProvider | None:
    if settings.food_provider == "disabled":
        return None
    from fitminiapp_api.services.open_food_facts import OpenFoodFactsProvider

    return OpenFoodFactsProvider(user_agent=settings.open_food_facts_user_agent)
