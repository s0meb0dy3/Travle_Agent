from abc import ABC, abstractmethod
from typing import Any


class LLMProvider(ABC):
    name: str

    @abstractmethod
    async def generate_json(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        raise NotImplementedError
