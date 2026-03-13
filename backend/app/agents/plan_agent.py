import logging
import time
from typing import Any
from uuid import uuid4

from pydantic import ValidationError

from app.core.errors import LLMOutputError
from app.integrations.siliconflow_client import SiliconFlowClient
from app.models.agent import AgentRunResult
from app.models.travel import TravelRequest, TravelResponse
from app.prompts.generate_itinerary import build_planner_messages
from app.services.fallback_service import FallbackService

logger = logging.getLogger(__name__)


class PlanAgent:
    def __init__(
        self,
        *,
        llm_client: SiliconFlowClient,
        fallback_service: FallbackService,
        provider_name: str,
        max_attempts: int = 2,
    ) -> None:
        self._llm_client = llm_client
        self._fallback_service = fallback_service
        self._provider_name = provider_name
        self._max_attempts = max_attempts

    async def generate_result(self, request: TravelRequest) -> TravelResponse:
        result, _ = await self._generate(request)
        return result

    async def run(self, request: TravelRequest) -> AgentRunResult:
        started_at = time.perf_counter()
        result, fallback_used = await self._generate(request)
        latency_ms = round((time.perf_counter() - started_at) * 1000, 2)

        return AgentRunResult(
            request_id=uuid4().hex,
            result=result,
            fallback_used=fallback_used,
            latency_ms=latency_ms,
            agent_name="plan",
            provider_name=self._provider_name,
        )

    async def _generate(self, request: TravelRequest) -> tuple[TravelResponse, bool]:
        last_error: Exception | None = None

        for attempt in range(1, self._max_attempts + 1):
            try:
                payload = await self._generate_with_llm(request)
                return self._build_response(payload, request.days), False
            except (LLMOutputError, ValidationError, ValueError) as exc:
                last_error = exc
                logger.warning(
                    "plan_agent_invalid_output attempt=%s destination=%s error=%s",
                    attempt,
                    request.destination,
                    exc,
                )

        logger.info(
            "plan_agent_fallback destination=%s reason=%s",
            request.destination,
            last_error,
        )
        return self._fallback_service.build(request), True

    async def _generate_with_llm(self, request: TravelRequest) -> dict[str, Any]:
        return await self._llm_client.generate_json(build_planner_messages(request))

    def _build_response(self, payload: dict[str, Any], expected_days: int) -> TravelResponse:
        normalized_payload = self._normalize_payload(payload, expected_days)
        response = TravelResponse.model_validate(normalized_payload)
        if len(response.plan.days) != expected_days:
            raise ValueError(f"Expected {expected_days} days but got {len(response.plan.days)}")
        return response

    @classmethod
    def _normalize_payload(cls, payload: dict[str, Any], expected_days: int) -> dict[str, Any]:
        normalized = dict(payload)
        normalized["mode"] = "itinerary"

        plan = normalized.get("plan")
        if not isinstance(plan, dict):
            raise LLMOutputError("LLM response is missing plan")

        raw_days = plan.get("days")
        if not isinstance(raw_days, list):
            raise LLMOutputError("LLM response is missing days")

        normalized_days: list[dict[str, Any]] = []
        for index, day in enumerate(raw_days[:expected_days]):
            if not isinstance(day, dict):
                continue
            normalized_days.append(
                {
                    "day": int(day.get("day", index + 1)),
                    "title": str(day.get("title") or f"Day {index + 1} 重点安排"),
                    "morning": cls._normalize_text(day.get("morning")),
                    "afternoon": cls._normalize_text(day.get("afternoon")),
                    "evening": cls._normalize_text(day.get("evening")),
                }
            )

        plan["days"] = normalized_days
        budget_breakdown = plan.get("budgetBreakdown")
        if isinstance(budget_breakdown, dict):
            plan["budgetBreakdown"] = {
                str(key): cls._normalize_text(value) or ""
                for key, value in budget_breakdown.items()
            }

        tips = normalized.get("tips")
        if isinstance(tips, str):
            normalized["tips"] = cls._split_tips(tips)
        elif isinstance(tips, list):
            normalized["tips"] = [
                cls._normalize_text(item)
                for item in tips
                if cls._normalize_text(item)
            ]
        else:
            normalized["tips"] = []

        return normalized

    @staticmethod
    def _normalize_text(value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @staticmethod
    def _split_tips(value: str) -> list[str]:
        normalized = value.replace("\n", " ").strip()
        parts = [
            item.strip(" .")
            for item in normalized.replace("；", "。").split("。")
            if item.strip()
        ]
        cleaned = []
        for item in parts:
            if len(item) > 2 and item[0].isdigit() and item[1] in {".", "、"}:
                cleaned.append(item[2:].strip())
            else:
                cleaned.append(item)
        return cleaned[:3]
