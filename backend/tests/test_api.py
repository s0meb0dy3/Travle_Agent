from fastapi.testclient import TestClient

from app.api.v1.dependencies import get_travel_service
from app.main import app
from app.schemas.travel import TravelResponse


class StubTravelService:
    async def generate_plan(self, request):  # noqa: ANN001
        return TravelResponse.model_validate(
            {
                "mode": "itinerary",
                "summary": f"{request.destination}{request.days}天轻松游",
                "plan": {
                    "days": [
                        {
                            "day": index + 1,
                            "title": f"Day {index + 1}",
                            "morning": "上午安排",
                            "afternoon": "下午安排",
                            "evening": "晚上安排",
                        }
                        for index in range(request.days)
                    ],
                    "budgetSummary": "预算约 1200 元 / 人",
                    "budgetBreakdown": {"交通": "300 元"},
                },
                "tips": ["注意防晒"],
            }
        )


client = TestClient(app)


def override_travel_service() -> StubTravelService:
    return StubTravelService()


app.dependency_overrides[get_travel_service] = override_travel_service


def test_healthz() -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_generate_plan_success() -> None:
    response = client.post(
        "/api/v1/generate",
        json={
            "origin": "上海",
            "destination": "杭州",
            "days": 2,
            "budget": "1000-1500",
            "style": ["relaxed", "photogenic"],
            "prompt": "周末想透透气，不想太累。",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "itinerary"
    assert len(body["plan"]["days"]) == 2


def test_generate_plan_invalid_days() -> None:
    response = client.post(
        "/api/v1/generate",
        json={"origin": "上海", "destination": "杭州", "days": 0},
    )
    assert response.status_code == 422


def test_generate_plan_invalid_style() -> None:
    response = client.post(
        "/api/v1/generate",
        json={"origin": "上海", "destination": "杭州", "days": 2, "style": ["party"]},
    )
    assert response.status_code == 422
