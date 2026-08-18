from __future__ import annotations

import time
from collections import deque
from collections.abc import Mapping
from decimal import Decimal, InvalidOperation
from threading import Lock
from typing import Any

import httpx

from fitminiapp_api.schemas.food import ServingUnit, validate_gtin
from fitminiapp_api.services.food_provider import FoodProviderUnavailable, ProviderFood

_API_BASE_URL = "https://world.openfoodfacts.org"
_SEARCH_URL = "https://search.openfoodfacts.org/search"
_FIELDS = (
    "code",
    "product_name",
    "brands",
    "nutriments",
    "serving_quantity",
    "serving_quantity_unit",
)
_LICENSE_URL = "https://opendatacommons.org/licenses/odbl/1-0/"
_RETRY_DELAY_SECONDS = 0.1


class _RequestBudget:
    def __init__(self, limit: int, *, window_seconds: float = 60.0) -> None:
        self._limit = limit
        self._window_seconds = window_seconds
        self._timestamps: deque[float] = deque()
        self._lock = Lock()

    def try_acquire(self) -> bool:
        now = time.monotonic()
        cutoff = now - self._window_seconds
        with self._lock:
            while self._timestamps and self._timestamps[0] <= cutoff:
                self._timestamps.popleft()
            if len(self._timestamps) >= self._limit:
                return False
            self._timestamps.append(now)
            return True


_SEARCH_REQUEST_BUDGET = _RequestBudget(10)
_PRODUCT_REQUEST_BUDGET = _RequestBudget(15)


class OpenFoodFactsProvider:
    name = "open_food_facts"

    def __init__(
        self,
        *,
        user_agent: str,
        timeout_seconds: float = 4.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._user_agent = user_agent
        self._timeout = httpx.Timeout(timeout_seconds)
        self._transport = transport

    def search(self, query: str, *, limit: int) -> list[ProviderFood]:
        normalized = " ".join(query.split())
        if len(normalized) < 2:
            return []
        payload = self._request_json(
            "POST",
            _SEARCH_URL,
            request_budget=_SEARCH_REQUEST_BUDGET,
            json={
                "q": self._plain_text_query(normalized),
                "page": 1,
                "page_size": min(limit, 20),
                "fields": list(_FIELDS),
                "langs": ["ru", "en"],
                "boost_phrase": True,
            },
        )
        raw_hits = payload.get("hits")
        if not isinstance(raw_hits, list):
            raise FoodProviderUnavailable("malformed_response")
        results: list[ProviderFood] = []
        for raw_hit in raw_hits:
            product = self._parse_product(raw_hit)
            if product is not None:
                results.append(product)
        return results

    def get_by_barcode(self, barcode: str) -> ProviderFood | None:
        payload = self._request_json(
            "GET",
            f"{_API_BASE_URL}/api/v3.6/product/{barcode}.json",
            request_budget=_PRODUCT_REQUEST_BUDGET,
            params={"fields": ",".join(_FIELDS)},
            allow_not_found=True,
        )
        if not payload:
            return None
        if payload.get("status") == 0:
            return None
        raw_product = payload.get("product")
        if raw_product is None:
            raise FoodProviderUnavailable("malformed_response")
        return self._parse_product(raw_product)

    def _request_json(
        self,
        method: str,
        url: str,
        *,
        request_budget: _RequestBudget,
        params: Mapping[str, str] | None = None,
        json: Mapping[str, Any] | None = None,
        allow_not_found: bool = False,
    ) -> dict[str, Any]:
        for attempt in range(2):
            if not request_budget.try_acquire():
                raise FoodProviderUnavailable("rate_limited")
            try:
                with httpx.Client(
                    headers={"User-Agent": self._user_agent, "Accept": "application/json"},
                    timeout=self._timeout,
                    transport=self._transport,
                    follow_redirects=False,
                    trust_env=False,
                ) as client:
                    response = client.request(method, url, params=params, json=json)
            except httpx.TimeoutException as exc:
                if attempt == 0:
                    time.sleep(_RETRY_DELAY_SECONDS)
                    continue
                raise FoodProviderUnavailable("timeout") from exc
            except httpx.RequestError as exc:
                if attempt == 0:
                    time.sleep(_RETRY_DELAY_SECONDS)
                    continue
                raise FoodProviderUnavailable("network_error") from exc

            if allow_not_found and response.status_code == 404:
                return {}
            if response.status_code == 429:
                raise FoodProviderUnavailable("rate_limited")
            if response.status_code >= 500:
                if attempt == 0:
                    time.sleep(_RETRY_DELAY_SECONDS)
                    continue
                raise FoodProviderUnavailable("upstream_error")
            if response.status_code >= 400:
                raise FoodProviderUnavailable("upstream_error")
            try:
                payload = response.json()
            except ValueError as exc:
                raise FoodProviderUnavailable("malformed_response") from exc
            if not isinstance(payload, dict):
                raise FoodProviderUnavailable("malformed_response")
            return payload
        raise AssertionError("request retry loop must return or raise")

    @staticmethod
    def _plain_text_query(query: str) -> str:
        escaped = query.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'

    @classmethod
    def _parse_product(cls, raw_product: object) -> ProviderFood | None:
        if not isinstance(raw_product, dict):
            return None
        nested_source = raw_product.get("_source")
        product = nested_source if isinstance(nested_source, dict) else raw_product

        raw_barcode = product.get("code")
        try:
            barcode = validate_gtin(str(raw_barcode)) if raw_barcode is not None else None
        except ValueError:
            return None
        name = cls._text(product.get("product_name"))
        if barcode is None or name is None:
            return None
        nutriments = product.get("nutriments")
        if not isinstance(nutriments, dict):
            return None
        energy = cls._nutrient(nutriments.get("energy-kcal_100g"), maximum=Decimal(1000))
        protein = cls._nutrient(nutriments.get("proteins_100g"), maximum=Decimal(100))
        fat = cls._nutrient(nutriments.get("fat_100g"), maximum=Decimal(100))
        carbs = cls._nutrient(nutriments.get("carbohydrates_100g"), maximum=Decimal(100))
        if any(value is None for value in (energy, protein, fat, carbs)):
            return None
        assert energy is not None
        assert protein is not None
        assert fat is not None
        assert carbs is not None
        fiber = cls._nutrient(nutriments.get("fiber_100g"), maximum=Decimal(100))

        serving_amount = cls._positive_decimal(product.get("serving_quantity"))
        serving_unit = cls._text(product.get("serving_quantity_unit"))
        standard_serving_unit: ServingUnit | None
        if serving_amount is None or serving_unit != "g":
            standard_serving_amount = None
            standard_serving_unit = None
            standard_serving_weight_g = None
        else:
            standard_serving_amount = serving_amount
            standard_serving_unit = "g"
            standard_serving_weight_g = serving_amount

        return ProviderFood(
            external_id=barcode,
            name=name,
            brand=cls._brand(product.get("brands")),
            barcode=barcode,
            energy_kcal_per_100g=energy,
            protein_g_per_100g=protein,
            fat_g_per_100g=fat,
            carbs_g_per_100g=carbs,
            fiber_g_per_100g=fiber,
            standard_serving_amount=standard_serving_amount,
            standard_serving_unit=standard_serving_unit,
            standard_serving_weight_g=standard_serving_weight_g,
            provider="open_food_facts",
            attribution="Open Food Facts contributors",
            source_url=f"{_API_BASE_URL}/product/{barcode}",
            license="ODbL-1.0",
            license_url=_LICENSE_URL,
        )

    @staticmethod
    def _text(value: object) -> str | None:
        if not isinstance(value, str):
            return None
        normalized = " ".join(value.split())
        return normalized or None

    @classmethod
    def _brand(cls, value: object) -> str | None:
        if isinstance(value, list):
            value = ", ".join(item for item in value if isinstance(item, str))
        return cls._text(value)

    @staticmethod
    def _positive_decimal(value: object) -> Decimal | None:
        parsed = OpenFoodFactsProvider._decimal(value)
        if parsed is None or parsed <= 0:
            return None
        return parsed

    @staticmethod
    def _nutrient(value: object, *, maximum: Decimal) -> Decimal | None:
        parsed = OpenFoodFactsProvider._decimal(value)
        if parsed is None or parsed < 0 or parsed > maximum:
            return None
        return parsed

    @staticmethod
    def _decimal(value: object) -> Decimal | None:
        if value is None or isinstance(value, bool):
            return None
        try:
            parsed = Decimal(str(value))
        except InvalidOperation, ValueError:
            return None
        return parsed if parsed.is_finite() else None
