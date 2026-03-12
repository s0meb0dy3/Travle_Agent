from typing import Any

from app.core.errors import LLMOutputError
from app.models.travel import TravelResponse


class PlanAssemblyService:
    def assemble(self, payload: dict[str, Any], expected_days: int) -> TravelResponse:
        normalized_payload = self._normalize_payload(payload, expected_days)
        result = TravelResponse.model_validate(normalized_payload)
        self._validate_day_count(result, expected_days)
        return result

    @staticmethod
    def _validate_day_count(result: TravelResponse, expected_days: int) -> None:
        if len(result.plan.days) != expected_days:
            raise ValueError(f"Expected {expected_days} days but got {len(result.plan.days)}")

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
                    "morning": PlanAssemblyService._normalize_text(day.get("morning")),
                    "afternoon": PlanAssemblyService._normalize_text(day.get("afternoon")),
                    "evening": PlanAssemblyService._normalize_text(day.get("evening")),
                }
            )

        plan["days"] = normalized_days
        budget_breakdown = plan.get("budgetBreakdown")
        if isinstance(budget_breakdown, dict):
            plan["budgetBreakdown"] = {
                str(key): PlanAssemblyService._normalize_text(value) or ""
                for key, value in budget_breakdown.items()
            }

        tips = normalized.get("tips")
        if isinstance(tips, str):
            normalized["tips"] = PlanAssemblyService._split_tips(tips)
        elif isinstance(tips, list):
            normalized["tips"] = [
                PlanAssemblyService._normalize_text(item)
                for item in tips
                if PlanAssemblyService._normalize_text(item)
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
