from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.travel import TravelRequest, TravelResponse


class AgentInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str
    request: TravelRequest


class AgentStep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    status: Literal["completed", "failed"]
    detail: str | None = None


class AgentContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str
    request: TravelRequest
    agent_name: str
    attempt: int = 0
    fallback_used: bool = False
    tool_results: dict[str, Any] = Field(default_factory=dict)
    tool_calls: list["ToolCallRecord"] = Field(default_factory=list)
    provider_calls: list["ProviderCallRecord"] = Field(default_factory=list)
    steps: list[AgentStep] = Field(default_factory=list)
    provider_name: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    debug: bool = False


class ToolCallRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tool_name: str
    retryable: bool = True
    success: bool


class ProviderCallRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider_name: str
    model_name: str | None = None
    success: bool


class AgentOutput(BaseModel):
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
