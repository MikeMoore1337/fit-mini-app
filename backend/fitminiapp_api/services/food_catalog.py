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


def _provider_failure_status(exc: FoodProviderUnavailable) -> FoodProviderStatus:
    return "rate_limited" if exc.reason == "rate_limited" else "unavailable"


def _provider_name(provider: FoodProvider) -> str:
    return getattr(provider, "name", "unknown")


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
        external_items = [serialize_provider_food(food) for food in external]
    except FoodProviderUnavailable as exc:
        logger.warning(
            "food_provider_search_unavailable",
            extra={"provider": _provider_name(provider), "reason": exc.reason},
        )
        return FoodSearchResponse(
            **response_values,
            provider_status=_provider_failure_status(exc),
        )
    return FoodSearchResponse(
        **response_values,
        external_items=external_items,
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
        return FoodBarcodeLookupResponse(
            barcode=barcode,
            status="found",
            source="local",
            local_item=local,
            provider_status="not_needed",
        )
    if provider is None:
        return FoodBarcodeLookupResponse(
            barcode=barcode,
            status="not_found",
            provider_status="disabled",
        )
    try:
        external = provider.get_by_barcode(barcode)
        external_item = serialize_provider_food(external) if external is not None else None
        if external_item is not None and external_item.barcode != barcode:
            raise FoodProviderUnavailable("malformed_response")
    except FoodProviderUnavailable as exc:
        logger.warning(
            "food_provider_barcode_unavailable",
            extra={"provider": _provider_name(provider), "reason": exc.reason},
        )
        return FoodBarcodeLookupResponse(
            barcode=barcode,
            status="not_found",
            provider_status=_provider_failure_status(exc),
        )
    if external_item is None:
        return FoodBarcodeLookupResponse(
            barcode=barcode,
            status="not_found",
            provider_status="available",
        )
    return FoodBarcodeLookupResponse(
        barcode=barcode,
        status="found",
        source="external",
        external_item=external_item,
        provider_status="available",
    )
