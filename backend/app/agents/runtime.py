import logging
from typing import Any, Literal

from app.models.agent import AgentContext, AgentStep

logger = logging.getLogger(__name__)


class AgentRuntime:
    def create_context(
        self,
        *,
        request_id: str,
        request: Any,
        agent_name: str,
        provider_name: str | None,
    ) -> AgentContext:
        return AgentContext(
            request_id=request_id,
            request=request,
            agent_name=agent_name,
            provider_name=provider_name,
        )

    @staticmethod
    def record_step(
        context: AgentContext,
        name: str,
        status: Literal["completed", "failed"],
        detail: str | None,
    ) -> None:
        context.steps.append(AgentStep(name=name, status=status, detail=detail))

    def log_trace(self, context: AgentContext, latency_ms: float) -> None:
        logger.info(
            "agent_run request_id=%s agent=%s provider=%s attempts=%s fallback=%s latency_ms=%s tools=%s steps=%s",
            context.request_id,
            context.agent_name,
            context.provider_name or "-",
            context.attempt,
            context.fallback_used,
            latency_ms,
            ",".join(call.tool_name for call in context.tool_calls) or "-",
            ",".join(step.name for step in context.steps) or "-",
        )
