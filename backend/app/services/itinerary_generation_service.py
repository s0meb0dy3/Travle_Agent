from pydantic import BaseModel, ConfigDict

from app.models.travel import TravelRequest
from app.providers.base import LLMProvider
from app.prompts.generate_itinerary import build_planner_messages


class LLMGenerateItineraryOutput(BaseModel):
    model_config = ConfigDict(extra="allow")

    mode: str | None = None
    summary: str | None = None
    plan: dict
    tips: list[str] | str | None = None


class ItineraryGenerationService:
    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider

    async def generate(self, request: TravelRequest) -> dict:
        return await self._provider.generate_json(build_planner_messages(request))
