from app.core.config import Settings
from app.providers.siliconflow import SiliconFlowProvider


class SiliconFlowClient:
    def __init__(self, settings: Settings) -> None:
        self._provider = SiliconFlowProvider(settings)

    async def generate_json(self, messages: list[dict[str, str]]) -> dict:
        return await self._provider.generate_json(messages)
