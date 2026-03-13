from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.models.travel import TravelResponse


class AgentRunResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str
    status: Literal["completed"] = "completed"
    result: TravelResponse
    fallback_used: bool = False
    latency_ms: float
    agent_name: str
    provider_name: str | None = None


class AgentPlanResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str
    status: Literal["completed"] = "completed"
    result: TravelResponse
