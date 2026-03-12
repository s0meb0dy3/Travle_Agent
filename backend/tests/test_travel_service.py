import httpx
import pytest

from app.core.config import Settings
from app.core.errors import LLMOutputError, ServiceUnavailableError, UpstreamServiceError
from app.integrations.siliconflow_client import SiliconFlowClient
from app.schemas.travel import TravelRequest
from app.services.fallback_service import FallbackService
from app.services.travel_service import TravelService


class InvalidThenValidClient:
    def __init__(self) -> None:
        self.calls = 0

    async def generate_json(self, messages):  # noqa: ANN001
        self.calls += 1
        if self.calls == 1:
            raise LLMOutputError("bad json")
        return {
            "mode": "itinerary",
            "summary": "杭州2天轻松漫游",
            "plan": {
                "days": [
                    {"day": 1, "title": "Day 1", "morning": "A", "afternoon": "B", "evening": "C"},
                    {"day": 2, "title": "Day 2", "morning": "A", "afternoon": "B", "evening": "C"},
                ],
                "budgetSummary": "约 1000 元 / 人",
                "budgetBreakdown": {"交通": "300 元"},
            },
            "tips": ["tip 1"],
        }


class AlwaysInvalidClient:
    async def generate_json(self, messages):  # noqa: ANN001
        raise LLMOutputError("still bad")


class TimeoutClient:
    async def generate_json(self, messages):  # noqa: ANN001
        raise UpstreamServiceError("timeout")


class NeedsNormalizationClient:
    async def generate_json(self, messages):  # noqa: ANN001
        return {
            "mode": "short_trip",
            "summary": "杭州2天轻松游",
            "plan": {
                "days": [
                    {"day": 1, "morning": "上午安排", "afternoon": "下午安排", "evening": "晚上安排"},
                    {"day": 2, "title": "Day 2", "morning": "上午安排", "afternoon": "下午安排", "evening": "晚上安排"},
                ],
                "budgetSummary": "预算约 1200 元 / 人",
                "budgetBreakdown": {"transportation": 300},
            },
            "tips": "1. 提前订票。2. 注意防晒。3. 别太赶。",
        }


@pytest.mark.asyncio
async def test_service_retries_and_succeeds() -> None:
    service = TravelService(client=InvalidThenValidClient(), fallback_service=FallbackService())
    request = TravelRequest(origin="上海", destination="杭州", days=2)

    result = await service.generate_plan(request)

    assert result.summary == "杭州2天轻松漫游"
    assert len(result.plan.days) == 2


@pytest.mark.asyncio
async def test_service_falls_back_after_invalid_output() -> None:
    service = TravelService(client=AlwaysInvalidClient(), fallback_service=FallbackService())
    request = TravelRequest(origin="上海", destination="杭州", days=2, style=["relaxed"])

    result = await service.generate_plan(request)

    assert result.summary == "杭州2天轻松漫游"
    assert len(result.plan.days) == 2


@pytest.mark.asyncio
async def test_service_raises_upstream_errors() -> None:
    service = TravelService(client=TimeoutClient(), fallback_service=FallbackService())
    request = TravelRequest(origin="上海", destination="杭州", days=2)

    with pytest.raises(UpstreamServiceError):
        await service.generate_plan(request)


@pytest.mark.asyncio
async def test_service_normalizes_llm_payload() -> None:
    service = TravelService(client=NeedsNormalizationClient(), fallback_service=FallbackService())
    request = TravelRequest(origin="上海", destination="杭州", days=2)

    result = await service.generate_plan(request)

    assert result.mode == "itinerary"
    assert result.plan.days[0].title == "Day 1 重点安排"
    assert result.plan.budgetBreakdown == {"transportation": "300"}
    assert result.tips == ["提前订票", "注意防晒", "别太赶"]


@pytest.mark.asyncio
async def test_siliconflow_client_requires_api_key() -> None:
    client = SiliconFlowClient(Settings(SILICONFLOW_API_KEY=None))

    with pytest.raises(ServiceUnavailableError):
        await client.generate_json([{"role": "user", "content": "ping"}])


@pytest.mark.asyncio
async def test_siliconflow_client_maps_unauthorized(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = Settings(SILICONFLOW_API_KEY="test-key")
    client = SiliconFlowClient(settings)

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):  # noqa: ANN002, ANN003
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):  # noqa: ANN001
            return False

        async def post(self, *args, **kwargs):  # noqa: ANN002, ANN003
            return httpx.Response(status_code=401, request=httpx.Request("POST", "https://example.com"))

    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)

    with pytest.raises(ServiceUnavailableError):
        await client.generate_json([{"role": "user", "content": "ping"}])
