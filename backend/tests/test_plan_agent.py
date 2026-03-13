import httpx
import pytest

from app.agents.plan_agent import PlanAgent
from app.core.config import Settings
from app.core.errors import LLMOutputError, ServiceUnavailableError, UpstreamServiceError
from app.integrations.siliconflow_client import SiliconFlowClient
from app.models.travel import TravelRequest
from app.services.fallback_service import FallbackService


class InvalidThenValidClient:
    def __init__(self) -> None:
        self.calls = 0

    async def generate_json(self, messages: list[dict[str, str]]) -> dict:  # noqa: ARG002
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
    async def generate_json(self, messages: list[dict[str, str]]) -> dict:  # noqa: ARG002
        raise LLMOutputError("still bad")


class TimeoutClient:
    async def generate_json(self, messages: list[dict[str, str]]) -> dict:  # noqa: ARG002
        raise UpstreamServiceError("timeout")


class NeedsNormalizationClient:
    async def generate_json(self, messages: list[dict[str, str]]) -> dict:  # noqa: ARG002
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


class WrongDayCountClient:
    async def generate_json(self, messages: list[dict[str, str]]) -> dict:  # noqa: ARG002
        return {
            "mode": "itinerary",
            "summary": "杭州2天轻松游",
            "plan": {
                "days": [{"day": 1, "title": "Day 1", "morning": "上午安排"}],
                "budgetSummary": "预算约 500 元 / 人",
                "budgetBreakdown": {"交通": "100 元"},
            },
            "tips": ["tip 1"],
        }


def build_agent(client) -> PlanAgent:  # noqa: ANN001
    return PlanAgent(
        llm_client=client,
        fallback_service=FallbackService(),
        provider_name="test-provider",
    )


@pytest.mark.asyncio
async def test_agent_retries_and_succeeds() -> None:
    agent = build_agent(InvalidThenValidClient())
    request = TravelRequest(origin="上海", destination="杭州", days=2)

    output = await agent.run(request)

    assert output.result.summary == "杭州2天轻松漫游"
    assert output.fallback_used is False
    assert output.agent_name == "plan"
    assert output.provider_name == "test-provider"
    assert len(output.result.plan.days) == 2


@pytest.mark.asyncio
async def test_agent_falls_back_after_invalid_output() -> None:
    agent = build_agent(AlwaysInvalidClient())
    request = TravelRequest(origin="上海", destination="杭州", days=2, style=["relaxed"])

    output = await agent.run(request)

    assert output.result.summary == "杭州2天轻松漫游"
    assert output.fallback_used is True
    assert len(output.result.plan.days) == 2


@pytest.mark.asyncio
async def test_agent_raises_upstream_errors() -> None:
    agent = build_agent(TimeoutClient())
    request = TravelRequest(origin="上海", destination="杭州", days=2)

    with pytest.raises(UpstreamServiceError):
        await agent.run(request)


@pytest.mark.asyncio
async def test_agent_normalizes_llm_payload() -> None:
    agent = build_agent(NeedsNormalizationClient())
    request = TravelRequest(origin="上海", destination="杭州", days=2)

    output = await agent.run(request)

    assert output.result.mode == "itinerary"
    assert output.result.plan.days[0].title == "Day 1 重点安排"
    assert output.result.plan.budgetBreakdown == {"transportation": "300"}
    assert output.result.tips == ["提前订票", "注意防晒", "别太赶"]


@pytest.mark.asyncio
async def test_agent_falls_back_when_day_count_is_wrong() -> None:
    agent = build_agent(WrongDayCountClient())
    request = TravelRequest(origin="上海", destination="杭州", days=2)

    output = await agent.run(request)

    assert output.fallback_used is True
    assert output.result.summary == "杭州2天轻松漫游"


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
