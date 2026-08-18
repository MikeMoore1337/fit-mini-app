from __future__ import annotations

from decimal import Decimal

import httpx
import pytest
from pydantic import ValidationError

from fitminiapp_api.core.config import Settings
from fitminiapp_api.db.session import get_session_context
from fitminiapp_api.main import app
from fitminiapp_api.models.food import Food
from fitminiapp_api.services import open_food_facts as off_module
from fitminiapp_api.services.food_provider import (
    FoodProviderUnavailable,
    ProviderFood,
    get_food_provider,
)
from fitminiapp_api.services.open_food_facts import OpenFoodFactsProvider


def _auth(client, telegram_user_id: int) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/dev-login",
        json={"telegram_user_id": telegram_user_id, "is_coach": False, "is_admin": False},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _provider_food(
    *, barcode: str = "3017620422003", name: str = "Тестовый продукт"
) -> ProviderFood:
    return ProviderFood(
        external_id=barcode,
        name=name,
        brand="Open brand",
        barcode=barcode,
        energy_kcal_per_100g=Decimal("120"),
        protein_g_per_100g=Decimal("5"),
        fat_g_per_100g=Decimal("3"),
        carbs_g_per_100g=Decimal("18"),
        fiber_g_per_100g=Decimal("2"),
        standard_serving_amount=Decimal("30"),
        standard_serving_unit="g",
        standard_serving_weight_g=Decimal("30"),
        provider="fake_food_catalog",
        attribution="Fake catalog contributors",
        source_url=f"https://catalog.example/products/{barcode}",
        license="Test-1.0",
        license_url="https://catalog.example/license",
    )


class FakeFoodProvider:
    def __init__(
        self,
        *,
        search_results: list[ProviderFood] | None = None,
        barcode_result: ProviderFood | None = None,
        failure: FoodProviderUnavailable | None = None,
    ) -> None:
        self.search_results = search_results or []
        self.barcode_result = barcode_result
        self.failure = failure
        self.search_calls = 0
        self.barcode_calls = 0

    def search(self, query: str, *, limit: int) -> list[ProviderFood]:
        del query, limit
        self.search_calls += 1
        if self.failure is not None:
            raise self.failure
        return self.search_results

    def get_by_barcode(self, barcode: str) -> ProviderFood | None:
        del barcode
        self.barcode_calls += 1
        if self.failure is not None:
            raise self.failure
        return self.barcode_result


def _override_provider(provider: FakeFoodProvider | None) -> None:
    app.dependency_overrides[get_food_provider] = lambda: provider


def _clear_provider_override() -> None:
    app.dependency_overrides.pop(get_food_provider, None)


def test_food_search_is_local_first_and_external_search_is_explicit(client) -> None:
    headers = _auth(client, 19_001)
    created = client.post(
        "/api/v1/nutrition/foods",
        headers=headers,
        json={
            "name": "Локальный кефир",
            "energy_kcal_per_100g": "52",
            "protein_g_per_100g": "3",
            "fat_g_per_100g": "2.5",
            "carbs_g_per_100g": "4",
        },
    )
    assert created.status_code == 201
    fake = FakeFoodProvider(search_results=[_provider_food()])
    _override_provider(fake)
    try:
        local = client.get(
            "/api/v1/nutrition/foods/search",
            headers=headers,
            params={"q": "кефир", "include_external": "true"},
        )
        not_requested = client.get(
            "/api/v1/nutrition/foods/search",
            headers=headers,
            params={"q": "редкий продукт"},
        )
    finally:
        _clear_provider_override()

    assert local.status_code == 200
    assert [item["id"] for item in local.json()["items"]] == [created.json()["id"]]
    assert local.json()["external_items"] == []
    assert local.json()["provider_status"] == "not_needed"
    assert not_requested.json()["provider_status"] == "not_requested"
    assert fake.search_calls == 0


def test_food_search_returns_separate_attributed_provider_results(client) -> None:
    headers = _auth(client, 19_002)
    fake = FakeFoodProvider(search_results=[_provider_food()])
    _override_provider(fake)
    try:
        response = client.get(
            "/api/v1/nutrition/foods/search",
            headers=headers,
            params={"q": "редкий продукт", "include_external": "true"},
        )
    finally:
        _clear_provider_override()

    assert response.status_code == 200
    payload = response.json()
    assert payload["items"] == []
    assert payload["provider_status"] == "available"
    assert payload["external_items"][0]["external_id"] == "3017620422003"
    assert payload["external_items"][0]["source"] == {
        "provider": "fake_food_catalog",
        "attribution": "Fake catalog contributors",
        "source_url": "https://catalog.example/products/3017620422003",
        "license": "Test-1.0",
        "license_url": "https://catalog.example/license",
    }
    assert fake.search_calls == 1


def test_barcode_lookup_is_local_first_and_private_scope_is_preserved(client) -> None:
    owner_headers = _auth(client, 19_003)
    other_headers = _auth(client, 19_004)
    barcode = "4006381333931"
    created = client.post(
        "/api/v1/nutrition/foods",
        headers=owner_headers,
        json={
            "name": "Личный продукт",
            "barcode": barcode,
            "energy_kcal_per_100g": "80",
            "protein_g_per_100g": "4",
            "fat_g_per_100g": "2",
            "carbs_g_per_100g": "12",
        },
    )
    assert created.status_code == 201
    fake = FakeFoodProvider(barcode_result=_provider_food(barcode=barcode))
    _override_provider(fake)
    try:
        owner_result = client.get(
            f"/api/v1/nutrition/foods/barcode/{barcode}", headers=owner_headers
        )
        other_result = client.get(
            f"/api/v1/nutrition/foods/barcode/{barcode}", headers=other_headers
        )
    finally:
        _clear_provider_override()

    assert owner_result.json()["local_item"]["id"] == created.json()["id"]
    assert owner_result.json()["provider_status"] == "not_needed"
    assert other_result.json()["local_item"] is None
    assert other_result.json()["external_item"]["barcode"] == barcode
    assert fake.barcode_calls == 1


@pytest.mark.parametrize(
    ("failure", "expected_status"),
    [
        (FoodProviderUnavailable("timeout"), "unavailable"),
        (FoodProviderUnavailable("rate_limited"), "rate_limited"),
    ],
)
def test_provider_failure_falls_back_without_touching_local_foods(
    client, failure: FoodProviderUnavailable, expected_status: str
) -> None:
    headers = _auth(client, 19_005)
    fake = FakeFoodProvider(failure=failure)
    _override_provider(fake)
    try:
        response = client.get(
            "/api/v1/nutrition/foods/search",
            headers=headers,
            params={"q": "не найдено", "include_external": "true"},
        )
    finally:
        _clear_provider_override()

    assert response.status_code == 200
    assert response.json()["items"] == []
    assert response.json()["external_items"] == []
    assert response.json()["provider_status"] == expected_status
    with get_session_context() as db:
        assert db.query(Food).count() == 0


def test_disabled_provider_and_invalid_barcode_have_safe_contract(client) -> None:
    headers = _auth(client, 19_006)
    _override_provider(None)
    try:
        search = client.get(
            "/api/v1/nutrition/foods/search",
            headers=headers,
            params={"q": "не найдено", "include_external": "true"},
        )
        barcode = client.get("/api/v1/nutrition/foods/barcode/12345678", headers=headers)
    finally:
        _clear_provider_override()

    assert search.status_code == 200
    assert search.json()["provider_status"] == "disabled"
    assert barcode.status_code == 422


def _off_product() -> dict[str, object]:
    return {
        "code": "3017620422003",
        "product_name": "Open product",
        "brands": "Open brand",
        "serving_quantity": 25,
        "serving_quantity_unit": "g",
        "nutriments": {
            "energy-kcal_100g": 120,
            "proteins_100g": 5,
            "fat_100g": 3,
            "carbohydrates_100g": 18,
            "fiber_100g": 2,
        },
    }


def test_open_food_facts_contract_uses_user_agent_and_parses_search_and_barcode() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.host == "search.openfoodfacts.org":
            return httpx.Response(200, request=request, json={"hits": [_off_product()]})
        return httpx.Response(
            200,
            request=request,
            json={"status": 1, "product": _off_product()},
        )

    provider = OpenFoodFactsProvider(
        user_agent="YourFitnessCoach/1.0 (ops@example.test)",
        transport=httpx.MockTransport(handler),
    )
    search_results = provider.search("open product", limit=50)
    barcode_result = provider.get_by_barcode("3017620422003")

    assert len(search_results) == 1
    assert search_results[0].source_url.endswith("/product/3017620422003")
    assert barcode_result is not None
    assert barcode_result.standard_serving_weight_g == Decimal("25")
    assert all(
        request.headers["user-agent"] == "YourFitnessCoach/1.0 (ops@example.test)"
        for request in requests
    )
    assert requests[0].method == "POST"
    assert requests[1].url.path == "/api/v3.6/product/3017620422003.json"


@pytest.mark.parametrize(
    ("responses", "expected_reason", "expected_calls"),
    [
        ([429], "rate_limited", 1),
        ([503, 503], "upstream_error", 2),
    ],
)
def test_open_food_facts_handles_rate_limit_and_bounded_5xx_retry(
    responses: list[int], expected_reason: str, expected_calls: int
) -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        status_code = responses[min(calls, len(responses) - 1)]
        calls += 1
        return httpx.Response(status_code, request=request)

    provider = OpenFoodFactsProvider(
        user_agent="YourFitnessCoach/1.0 (ops@example.test)",
        transport=httpx.MockTransport(handler),
    )
    with pytest.raises(FoodProviderUnavailable) as exc_info:
        provider.search("product", limit=10)
    assert exc_info.value.reason == expected_reason
    assert calls == expected_calls


def test_open_food_facts_enforces_documented_search_budget(monkeypatch) -> None:
    monkeypatch.setattr(off_module, "_SEARCH_REQUEST_BUDGET", off_module._RequestBudget(1))
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, request=request, json={"hits": []})

    provider = OpenFoodFactsProvider(
        user_agent="YourFitnessCoach/1.0 (ops@example.test)",
        transport=httpx.MockTransport(handler),
    )
    assert provider.search("first", limit=10) == []
    with pytest.raises(FoodProviderUnavailable) as exc_info:
        provider.search("second", limit=10)
    assert exc_info.value.reason == "rate_limited"
    assert calls == 1


def test_open_food_facts_retries_timeout_and_rejects_malformed_response() -> None:
    timeout_calls = 0

    def timeout_handler(request: httpx.Request) -> httpx.Response:
        nonlocal timeout_calls
        timeout_calls += 1
        raise httpx.ReadTimeout("upstream timeout", request=request)

    timeout_provider = OpenFoodFactsProvider(
        user_agent="YourFitnessCoach/1.0 (ops@example.test)",
        transport=httpx.MockTransport(timeout_handler),
    )
    with pytest.raises(FoodProviderUnavailable) as timeout_error:
        timeout_provider.search("product", limit=10)
    assert timeout_error.value.reason == "timeout"
    assert timeout_calls == 2

    malformed_provider = OpenFoodFactsProvider(
        user_agent="YourFitnessCoach/1.0 (ops@example.test)",
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, request=request, json={})
        ),
    )
    with pytest.raises(FoodProviderUnavailable) as malformed_error:
        malformed_provider.search("product", limit=10)
    assert malformed_error.value.reason == "malformed_response"


def test_open_food_facts_retries_network_error_with_safe_classification() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise httpx.ConnectError("upstream unavailable", request=request)

    provider = OpenFoodFactsProvider(
        user_agent="YourFitnessCoach/1.0 (ops@example.test)",
        transport=httpx.MockTransport(handler),
    )
    with pytest.raises(FoodProviderUnavailable) as exc_info:
        provider.get_by_barcode("3017620422003")
    assert exc_info.value.reason == "network_error"
    assert calls == 2


def test_open_food_facts_requires_identifying_user_agent_when_enabled() -> None:
    common = {
        "app_env": "dev",
        "app_name": "Your Fitness Coach",
        "app_debug": False,
        "secret_key": "test-secret",
        "access_token_expire_minutes": 60,
        "refresh_token_expire_days": 30,
        "database_url": "sqlite://",
        "telegram_bot_token": "test-token",
    }
    with pytest.raises(ValidationError, match="OPEN_FOOD_FACTS_USER_AGENT"):
        Settings(**common, food_provider="open_food_facts")
    configured = Settings(
        **common,
        food_provider="open_food_facts",
        open_food_facts_user_agent="YourFitnessCoach/1.0 (ops@example.test)",
    )
    assert configured.food_provider == "open_food_facts"
