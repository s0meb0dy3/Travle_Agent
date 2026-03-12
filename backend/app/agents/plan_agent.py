import logging
from typing import Any

from app.agents.base import BaseAgent
from app.agents.runtime import AgentRuntime
from app.models.agent import AgentContext, AgentInput
from app.models.travel import TravelRequest, TravelResponse
from app.services.fallback_service import FallbackService
from app.services.plan_assembly_service import PlanAssemblyService
from app.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class PlanAgent(BaseAgent[TravelRequest, TravelResponse]):
    def __init__(
        self,
        *,
        tool_registry: ToolRegistry,
        runtime: AgentRuntime,
        plan_assembly_service: PlanAssemblyService,
        fallback_service: FallbackService,
        provider_name: str,
    ) -> None:
        super().__init__(
            name="plan",
            tool_registry=tool_registry,
            runtime=runtime,
            provider_name=provider_name,
        )
        self._plan_assembly_service = plan_assembly_service
        self._fallback_service = fallback_service

    def build_goal(self, agent_input: AgentInput) -> str:
        return f"Generate a travel itinerary for {agent_input.request.destination} in {agent_input.request.days} days."

    async def plan(self, context: AgentContext) -> str:
        return "llm_generate_itinerary"

    async def act(self, context: AgentContext, plan: str) -> Any:
        return await self.execute_tool(context, plan, context.request)

    async def observe(self, context: AgentContext, observation: Any) -> TravelResponse:
        result = self._plan_assembly_service.assemble(observation, context.request.days)
        AgentRuntime.record_step(context, "observe", "completed", "validated_travel_response")
        return result

    async def fallback_if_needed(self, context: AgentContext, error: Exception | None) -> TravelResponse:
        context.fallback_used = True
        if error:
            logger.info(
                "agent_fallback request_id=%s agent=%s destination=%s reason=%s",
                context.request_id,
                context.agent_name,
                context.request.destination,
                error,
            )
        AgentRuntime.record_step(context, "fallback_if_needed", "completed", "fallback_template")
        return self._fallback_service.build(context.request)
