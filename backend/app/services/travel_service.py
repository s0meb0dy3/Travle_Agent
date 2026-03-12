import logging
import time
from typing import Any

from pydantic import ValidationError

from app.core.errors import LLMOutputError
from app.integrations.siliconflow_client import SiliconFlowClient
from app.prompts.generate_itinerary import build_generate_messages
from app.schemas.travel import TravelRequest, TravelResponse
from app.services.fallback_service import FallbackService

logger = logging.getLogger(__name__)


class TravelService:
    def __init__(
        self,
        client: SiliconFlowClient,
        fallback_service: FallbackService | None = None,
    ) -> None:
        self._client = client
        self._fallback_service = fallback_service or FallbackService()

    async def generate_plan(self, request: TravelRequest) -> TravelResponse:
        started_at = time.perf_counter()
        used_fallback = False
        last_error: Exception | None = None

        for attempt in range(2):
            try:
                payload = await self._client.generate_json(build_generate_messages(request))
                normalized_payload = self._normalize_payload(payload, request.days)
                result = TravelResponse.model_validate(normalized_payload)
                self._validate_day_count(result, request.days)
                self._log_result(request, used_fallback=False, elapsed=time.perf_counter() - started_at)
                return result
            except (LLMOutputError, ValidationError, ValueError) as exc:
                last_error = exc
                logger.warning(
                    "llm_output_invalid destination=%s days=%s attempt=%s error=%s",
                    request.destination,
                    request.days,
                    attempt + 1,
                    exc,
                )

        used_fallback = True
        result = self._fallback_service.build(request)
        self._log_result(request, used_fallback=used_fallback, elapsed=time.perf_counter() - started_at)
        if last_error:
            logger.info("fallback_triggered destination=%s reason=%s", request.destination, last_error)
        return result

    @staticmethod
    def _validate_day_count(result: TravelResponse, expected_days: int) -> None:
        if len(result.plan.days) != expected_days:
            raise ValueError(f"Expected {expected_days} days but got {len(result.plan.days)}")

    def _log_result(self, request: TravelRequest, used_fallback: bool, elapsed: float) -> None:
        logger.info(
            "generate_plan destination=%s days=%s styles=%s fallback=%s elapsed_ms=%s",
            request.destination,
            request.days,
            ",".join(item.value for item in request.style or []) or "-",
            used_fallback,
            round(elapsed * 1000, 2),
        )

    @staticmethod
    def _normalize_payload(payload: dict[str, Any], expected_days: int) -> dict[str, Any]:
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
                    "morning": TravelService._normalize_text(day.get("morning")),
                    "afternoon": TravelService._normalize_text(day.get("afternoon")),
                    "evening": TravelService._normalize_text(day.get("evening")),
                }
            )

        plan["days"] = normalized_days
        budget_breakdown = plan.get("budgetBreakdown")
        if isinstance(budget_breakdown, dict):
            plan["budgetBreakdown"] = {
                str(key): TravelService._normalize_text(value) or ""
                for key, value in budget_breakdown.items()
            }

        tips = normalized.get("tips")
        if isinstance(tips, str):
            normalized["tips"] = TravelService._split_tips(tips)
        elif isinstance(tips, list):
            normalized["tips"] = [
                TravelService._normalize_text(item)
                for item in tips
                if TravelService._normalize_text(item)
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
