from functools import lru_cache

from app.core.config import Settings, get_settings
from app.integrations.siliconflow_client import SiliconFlowClient
from app.services.fallback_service import FallbackService
from app.services.travel_service import TravelService


@lru_cache
def get_siliconflow_client() -> SiliconFlowClient:
    settings: Settings = get_settings()
    return SiliconFlowClient(settings)


@lru_cache
def get_fallback_service() -> FallbackService:
    return FallbackService()


def get_travel_service() -> TravelService:
    return TravelService(
        client=get_siliconflow_client(),
        fallback_service=get_fallback_service(),
    )
