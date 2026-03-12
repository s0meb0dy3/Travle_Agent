import json
from typing import Any

import httpx

from app.core.config import Settings
from app.core.errors import LLMOutputError, ServiceUnavailableError, UpstreamServiceError


class SiliconFlowClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def generate_json(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        if not self._settings.siliconflow_api_key:
            raise ServiceUnavailableError("缺少 SILICONFLOW_API_KEY，暂时无法生成行程。")

        payload = {
            "model": self._settings.llm_model,
            "temperature": 0.2,
            "max_tokens": 900,
            "response_format": {"type": "json_object"},
            "messages": messages,
        }

        headers = {
            "Authorization": f"Bearer {self._settings.siliconflow_api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(
                base_url=self._settings.llm_base_url,
                timeout=self._settings.llm_timeout_seconds,
            ) as client:
                response = await client.post("/chat/completions", headers=headers, json=payload)
        except httpx.TimeoutException as exc:
            raise UpstreamServiceError("行程生成超时，请稍后再试。") from exc
        except httpx.RequestError as exc:
            raise UpstreamServiceError("行程生成服务暂时不可用，请稍后再试。") from exc

        if response.status_code in {401, 403}:
            raise ServiceUnavailableError("模型服务鉴权失败，请检查后端配置。")
        if response.status_code >= 500:
            raise UpstreamServiceError("上游模型服务暂时不可用，请稍后再试。")
        if response.status_code >= 400:
            raise UpstreamServiceError("模型服务请求失败，请稍后再试。")

        data = response.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMOutputError("LLM response is missing content") from exc

        return self._extract_json(content)

    def _extract_json(self, content: str) -> dict[str, Any]:
        text = content.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.startswith("json"):
                text = text[4:].strip()

        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end < start:
            raise LLMOutputError("LLM response does not contain JSON")

        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError as exc:
            raise LLMOutputError("LLM response contains invalid JSON") from exc
