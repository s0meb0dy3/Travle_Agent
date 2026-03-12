import httpx
import pytest

from app.agents.plan_agent import PlanAgent
from app.agents.registry import AgentRegistry
from app.agents.runtime import AgentRuntime
from app.core.config import Settings
from app.core.errors import LLMOutputError, ServiceUnavailableError, UpstreamServiceError
from app.integrations.siliconflow_client import SiliconFlowClient
from app.models.travel import TravelRequest, TravelResponse
from app.providers.registry import ProviderRegistry
from app.providers.siliconflow import SiliconFlowProvider
from app.services.fallback_service import FallbackService
from app.services.itinerary_generation_service import LLMGenerateItineraryOutput
from app.services.plan_assembly_service import PlanAssemblyService
from app.tools.adapters import tool_spec_to_openai_tool_schema
from app.tools.base import ToolContext, ToolSpec
from app.tools.registry import ToolRegistry


class InvalidThenValidExecutor:
    def __init__(self) -> None:
        self.calls = 0

    async def __call__(self, request: TravelRequest, context: ToolContext):  # noqa: ARG002
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


class AlwaysInvalidExecutor:
    async def __call__(self, request: TravelRequest, context: ToolContext):  # noqa: ARG002
        raise LLMOutputError("still bad")


class TimeoutExecutor:
    async def __call__(self, request: TravelRequest, context: ToolContext):  # noqa: ARG002
        raise UpstreamServiceError("timeout")


class NeedsNormalizationExecutor:
    async def __call__(self, request: TravelRequest, context: ToolContext):  # noqa: ARG002
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


def build_tool_registry(executor) -> ToolRegistry:  # noqa: ANN001
    registry = ToolRegistry()
    registry.register(
        ToolSpec(
            name="llm_generate_itinerary",
            description="Generate itinerary",
            input_model=TravelRequest,
            output_model=LLMGenerateItineraryOutput,
            executor=executor,
            retryable=True,
        )
    )
    return registry


def build_agent(executor) -> PlanAgent:  # noqa: ANN001
    return PlanAgent(
        tool_registry=build_tool_registry(executor),
        runtime=AgentRuntime(),
        plan_assembly_service=PlanAssemblyService(),
        fallback_service=FallbackService(),
        provider_name="test-provider",
    )


@pytest.mark.asyncio
async def test_agent_retries_and_succeeds() -> None:
    agent = build_agent(InvalidThenValidExecutor())
    request = TravelRequest(origin="上海", destination="杭州", days=2)

    output = await agent.run(request)

    assert output.result.summary == "杭州2天轻松漫游"
    assert output.fallback_used is False
    assert output.agent_name == "plan"
    assert output.provider_name == "test-provider"
    assert len(output.result.plan.days) == 2


@pytest.mark.asyncio
async def test_agent_falls_back_after_invalid_output() -> None:
    agent = build_agent(AlwaysInvalidExecutor())
    request = TravelRequest(origin="上海", destination="杭州", days=2, style=["relaxed"])

    output = await agent.run(request)

    assert output.result.summary == "杭州2天轻松漫游"
    assert output.fallback_used is True
    assert len(output.result.plan.days) == 2


@pytest.mark.asyncio
async def test_agent_raises_upstream_errors() -> None:
    agent = build_agent(TimeoutExecutor())
    request = TravelRequest(origin="上海", destination="杭州", days=2)

    with pytest.raises(UpstreamServiceError):
        await agent.run(request)


@pytest.mark.asyncio
async def test_agent_normalizes_llm_payload() -> None:
    agent = build_agent(NeedsNormalizationExecutor())
    request = TravelRequest(origin="上海", destination="杭州", days=2)

    output = await agent.run(request)

    assert output.result.mode == "itinerary"
    assert output.result.plan.days[0].title == "Day 1 重点安排"
    assert output.result.plan.budgetBreakdown == {"transportation": "300"}
    assert output.result.tips == ["提前订票", "注意防晒", "别太赶"]


def test_agent_registry_returns_registered_agent() -> None:
    agent = build_agent(NeedsNormalizationExecutor())
    registry = AgentRegistry()
    registry.register("plan", agent)

    assert registry.get("plan") is agent


@pytest.mark.asyncio
async def test_tool_registry_executes_and_validates_schema() -> None:
    async def executor(request: TravelRequest, context: ToolContext):  # noqa: ARG001
        return {
            "mode": "itinerary",
            "summary": f"{request.destination}{request.days}天轻松游",
            "plan": {
                "days": [{"day": 1, "title": "Day 1"}],
                "budgetSummary": "预算约 500 元 / 人",
                "budgetBreakdown": {"交通": "100 元"},
            },
            "tips": ["tip 1"],
        }

    registry = build_tool_registry(executor)

    class DummyContext:
        def __init__(self) -> None:
            self.request_id = "req-1"
            self.agent_name = "plan"
            self.provider_name = "siliconflow"
            self.tool_results = {}
            self.tool_calls = []

    context = DummyContext()
    result = await registry.execute(
        "llm_generate_itinerary",
        TravelRequest(origin="上海", destination="杭州", days=1),
        context,
    )

    assert result["mode"] == "itinerary"
    assert context.tool_calls[0].tool_name == "llm_generate_itinerary"


def test_tool_spec_to_openai_tool_schema() -> None:
    async def executor(request: TravelRequest, context: ToolContext):  # noqa: ARG001
        return {"mode": "itinerary", "summary": "ok", "plan": {"days": [{"day": 1, "title": "D1"}]}}

    tool = ToolSpec(
        name="llm_generate_itinerary",
        description="Generate itinerary",
        input_model=TravelRequest,
        output_model=LLMGenerateItineraryOutput,
        executor=executor,
    )

    schema = tool_spec_to_openai_tool_schema(tool)

    assert schema["type"] == "function"
    assert schema["function"]["name"] == "llm_generate_itinerary"


def test_provider_registry_returns_default_provider() -> None:
    registry = ProviderRegistry(default_provider="siliconflow")
    provider = SiliconFlowProvider(Settings(SILICONFLOW_API_KEY="test-key"))
    registry.register(provider)

    assert registry.get() is provider


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
