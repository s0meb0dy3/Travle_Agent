from functools import lru_cache

from app.agents.plan_agent import PlanAgent
from app.core.config import Settings, get_settings
from app.integrations.siliconflow_client import SiliconFlowClient
from app.services.fallback_service import FallbackService


@lru_cache
def get_siliconflow_client() -> SiliconFlowClient:
    settings: Settings = get_settings()
    return SiliconFlowClient(settings)


@lru_cache
def get_fallback_service() -> FallbackService:
    return FallbackService()


@lru_cache
@lru_cache
def get_plan_agent() -> PlanAgent:
    return PlanAgent(
        llm_client=get_siliconflow_client(),
        fallback_service=get_fallback_service(),
        provider_name="siliconflow",
    )
