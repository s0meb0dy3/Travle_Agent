import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar
from uuid import uuid4

from pydantic import ValidationError

from app.agents.runtime import AgentRuntime
from app.core.errors import LLMOutputError
from app.models.agent import AgentContext, AgentInput, AgentOutput
from app.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)

RequestT = TypeVar("RequestT")
ResultT = TypeVar("ResultT")


class BaseAgent(ABC, Generic[RequestT, ResultT]):
    def __init__(
        self,
        *,
        name: str,
        tool_registry: ToolRegistry,
        runtime: AgentRuntime,
        provider_name: str | None = None,
        max_attempts: int = 2,
    ) -> None:
        self._name = name
        self._tool_registry = tool_registry
        self._runtime = runtime
        self._provider_name = provider_name
        self._max_attempts = max_attempts

    async def run(self, request: RequestT) -> AgentOutput:
        started_at = time.perf_counter()
        agent_input = AgentInput(request_id=uuid4().hex, request=request)
        context = self._runtime.create_context(
            request_id=agent_input.request_id,
            request=request,
            agent_name=self._name,
            provider_name=self._provider_name,
        )

        goal = self.build_goal(agent_input)
        self._runtime.record_step(context, "build_goal", "completed", goal)

        plan = await self.plan(context)
        self._runtime.record_step(context, "plan", "completed", plan)

        last_error: Exception | None = None
        for attempt in range(1, self._max_attempts + 1):
            context.attempt = attempt
            try:
                observation = await self.act(context, plan)
                result = await self.observe(context, observation)
                finalized = await self.finalize(context, result)
                self._runtime.record_step(context, "finalize", "completed", "final_result")
                latency_ms = round((time.perf_counter() - started_at) * 1000, 2)
                self._runtime.log_trace(context, latency_ms)
                return AgentOutput(
                    request_id=context.request_id,
                    result=finalized,
                    fallback_used=context.fallback_used,
                    latency_ms=latency_ms,
                    agent_name=context.agent_name,
                    provider_name=context.provider_name,
                )
            except (LLMOutputError, ValidationError, ValueError) as exc:
                last_error = exc
                self._runtime.record_step(context, "observe", "failed", str(exc))
                logger.warning(
                    "agent_observe_failed request_id=%s agent=%s attempt=%s error=%s",
                    context.request_id,
                    context.agent_name,
                    context.attempt,
                    exc,
                )

        fallback_result = await self.fallback_if_needed(context, last_error)
        latency_ms = round((time.perf_counter() - started_at) * 1000, 2)
        self._runtime.log_trace(context, latency_ms)
        return AgentOutput(
            request_id=context.request_id,
            result=fallback_result,
            fallback_used=context.fallback_used,
            latency_ms=latency_ms,
            agent_name=context.agent_name,
            provider_name=context.provider_name,
        )

    async def execute_tool(self, context: AgentContext, tool_name: str, payload: Any) -> Any:
        return await self._tool_registry.execute(tool_name, payload, context)

    @abstractmethod
    def build_goal(self, agent_input: AgentInput) -> str:
        raise NotImplementedError

    @abstractmethod
    async def plan(self, context: AgentContext) -> str:
        raise NotImplementedError

    @abstractmethod
    async def act(self, context: AgentContext, plan: str) -> Any:
        raise NotImplementedError

    @abstractmethod
    async def observe(self, context: AgentContext, observation: Any) -> ResultT:
        raise NotImplementedError

    async def finalize(self, context: AgentContext, result: ResultT) -> ResultT:
        return result

    @abstractmethod
    async def fallback_if_needed(self, context: AgentContext, error: Exception | None) -> ResultT:
        raise NotImplementedError
