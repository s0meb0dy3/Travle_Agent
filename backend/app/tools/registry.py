from typing import Any

from app.models.agent import ToolCallRecord
from app.tools.base import ToolContext, ToolSpec


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}

    def register(self, tool: ToolSpec) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolSpec:
        if name not in self._tools:
            raise KeyError(f"Unknown tool: {name}")
        return self._tools[name]

    async def execute(self, name: str, payload: Any, agent_context) -> dict[str, Any]:  # noqa: ANN001
        tool = self.get(name)
        input_payload = tool.input_model.model_validate(payload)
        context = ToolContext(
            request_id=agent_context.request_id,
            agent_name=agent_context.agent_name,
            provider_name=agent_context.provider_name,
        )
        result = await tool.executor(input_payload, context)
        output_payload = (
            tool.output_model.model_validate(result).model_dump()
            if isinstance(result, dict)
            else tool.output_model.model_validate(result).model_dump()
        )
        agent_context.tool_results[name] = output_payload
        agent_context.tool_calls.append(
            ToolCallRecord(
                tool_name=name,
                retryable=tool.retryable,
                success=True,
            )
        )
        return output_payload
