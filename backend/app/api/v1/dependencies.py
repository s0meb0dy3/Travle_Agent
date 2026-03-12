from functools import lru_cache

from app.agents.plan_agent import PlanAgent
from app.agents.registry import AgentRegistry
from app.agents.runtime import AgentRuntime
from app.core.config import Settings, get_settings
from app.models.travel import TravelRequest
from app.providers.registry import ProviderRegistry
from app.providers.siliconflow import SiliconFlowProvider
from app.services.fallback_service import FallbackService
from app.services.itinerary_generation_service import ItineraryGenerationService, LLMGenerateItineraryOutput
from app.services.plan_assembly_service import PlanAssemblyService
from app.tools.base import ToolContext, ToolSpec
from app.tools.registry import ToolRegistry


@lru_cache
def get_provider_registry() -> ProviderRegistry:
    settings: Settings = get_settings()
    registry = ProviderRegistry(default_provider="siliconflow")
    registry.register(SiliconFlowProvider(settings))
    return registry


@lru_cache
def get_fallback_service() -> FallbackService:
    return FallbackService()


@lru_cache
def get_itinerary_generation_service() -> ItineraryGenerationService:
    return ItineraryGenerationService(provider=get_provider_registry().get())


@lru_cache
def get_plan_assembly_service() -> PlanAssemblyService:
    return PlanAssemblyService()


@lru_cache
def get_agent_runtime() -> AgentRuntime:
    return AgentRuntime()


async def llm_generate_itinerary_executor(
    request: TravelRequest,
    context: ToolContext,  # noqa: ARG001
) -> dict:
    return await get_itinerary_generation_service().generate(request)


def get_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(
        ToolSpec(
            name="llm_generate_itinerary",
            description="Generate a structured travel itinerary with the configured LLM provider.",
            input_model=TravelRequest,
            output_model=LLMGenerateItineraryOutput,
            executor=llm_generate_itinerary_executor,
            retryable=True,
            timeout_seconds=get_settings().llm_timeout_seconds,
        )
    )
    return registry


def get_agent_registry() -> AgentRegistry:
    registry = AgentRegistry()
    registry.register(
        "plan",
        PlanAgent(
            tool_registry=get_tool_registry(),
            runtime=get_agent_runtime(),
            plan_assembly_service=get_plan_assembly_service(),
            fallback_service=get_fallback_service(),
            provider_name=get_provider_registry().default_provider,
        ),
    )
    return registry


def get_plan_agent() -> PlanAgent:
    return get_agent_registry().get("plan")  # type: ignore[return-value]
