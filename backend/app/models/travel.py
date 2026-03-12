from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TravelStyle(str, Enum):
    RELAXED = "relaxed"
    PHOTOGENIC = "photogenic"
    FOODIE = "foodie"
    CITY_WALK = "city walk"
    NATURE = "nature"


class TravelRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    origin: str = Field(min_length=1)
    destination: str = Field(min_length=1)
    days: int = Field(ge=1, le=7)
    budget: str | None = None
    style: list[TravelStyle] | None = None
    prompt: str | None = None

    @field_validator("origin", "destination", "budget", "prompt", mode="before")
    @classmethod
    def strip_strings(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip()

    @field_validator("origin", "destination")
    @classmethod
    def require_non_empty(cls, value: str) -> str:
        if not value:
            raise ValueError("must not be empty")
        return value

    @field_validator("style")
    @classmethod
    def dedupe_style(cls, value: list[TravelStyle] | None) -> list[TravelStyle] | None:
        if value is None:
            return value
        seen: list[TravelStyle] = []
        for item in value:
            if item not in seen:
                seen.append(item)
        return seen


class ItineraryDay(BaseModel):
    model_config = ConfigDict(extra="forbid")

    day: int = Field(ge=1)
    title: str = Field(min_length=1)
    morning: str | None = None
    afternoon: str | None = None
    evening: str | None = None


class TravelPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    days: list[ItineraryDay]
    budgetSummary: str | None = None
    budgetBreakdown: dict[str, str] | None = None


class TravelResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: str = "itinerary"
    summary: str = Field(min_length=1)
    plan: TravelPlan
    tips: list[str] | None = None

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, value: str) -> str:
        if value != "itinerary":
            raise ValueError("mode must be itinerary")
        return value

    @field_validator("tips")
    @classmethod
    def limit_tips(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return value
        filtered = [tip.strip() for tip in value if tip and tip.strip()]
        return filtered[:3]
