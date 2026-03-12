from collections.abc import Awaitable, Callable
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict

InputModelT = TypeVar("InputModelT", bound=BaseModel)
OutputModelT = TypeVar("OutputModelT", bound=BaseModel)


class ToolContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str
    agent_name: str
    provider_name: str | None = None


class ToolSpec(Generic[InputModelT, OutputModelT]):
    def __init__(
        self,
        *,
        name: str,
        description: str,
        input_model: type[InputModelT],
        output_model: type[OutputModelT],
        executor: Callable[[InputModelT, ToolContext], Awaitable[dict[str, Any] | OutputModelT]],
        retryable: bool = True,
        timeout_seconds: float | None = None,
    ) -> None:
        self.name = name
        self.description = description
        self.input_model = input_model
        self.output_model = output_model
        self.executor = executor
        self.retryable = retryable
        self.timeout_seconds = timeout_seconds
