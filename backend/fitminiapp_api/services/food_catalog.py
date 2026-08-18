import logging

from sqlalchemy.orm import Session

from fitminiapp_api.models.user import User
from fitminiapp_api.schemas.food import (
    FoodBarcodeLookupResponse,
    FoodProviderStatus,
    FoodSearchResponse,
)
from fitminiapp_api.services.food_provider import (
    FoodProvider,
    FoodProviderUnavailable,
    serialize_provider_food,
)
from fitminiapp_api.services.foods import (
    get_food_by_barcode_response,
    search_foods,
)

logger = logging.getLogger("app")


def search_food_catalog(
    db: Session,
    current_user: User,
    query_text: str,
    *,
    limit: int,
    offset: int,
    include_external: bool,
    provider: FoodProvider | None,
) -> FoodSearchResponse:
    local = search_foods(db, current_user, query_text, limit=limit, offset=offset)
    response_values = local.model_dump()
    if local.total > 0:
        return FoodSearchResponse(**response_values, provider_status="not_needed")
    if not include_external or offset > 0:
        return FoodSearchResponse(**response_values, provider_status="not_requested")
    if provider is None:
        return FoodSearchResponse(**response_values, provider_status="disabled")
    try:
        external = provider.search(query_text, limit=min(limit, 20))
    except FoodProviderUnavailable as exc:
        logger.warning("food_provider_search_unavailable", extra={"reason": exc.reason})
        status: FoodProviderStatus = (
            "rate_limited" if exc.reason == "rate_limited" else "unavailable"
        )
        return FoodSearchResponse(**response_values, provider_status=status)
    return FoodSearchResponse(
        **response_values,
        external_items=[serialize_provider_food(food) for food in external],
        provider_status="available",
    )


def get_food_catalog_item_by_barcode(
    db: Session,
    current_user: User,
    barcode: str,
    *,
    provider: FoodProvider | None,
) -> FoodBarcodeLookupResponse:
    local = get_food_by_barcode_response(db, current_user, barcode)
    if local is not None:
        return FoodBarcodeLookupResponse(local_item=local, provider_status="not_needed")
    if provider is None:
        return FoodBarcodeLookupResponse(provider_status="disabled")
    try:
        external = provider.get_by_barcode(barcode)
    except FoodProviderUnavailable as exc:
        logger.warning("food_provider_barcode_unavailable", extra={"reason": exc.reason})
        status: FoodProviderStatus = (
            "rate_limited" if exc.reason == "rate_limited" else "unavailable"
        )
        return FoodBarcodeLookupResponse(provider_status=status)
    return FoodBarcodeLookupResponse(
        external_item=serialize_provider_food(external) if external is not None else None,
        provider_status="available",
    )
