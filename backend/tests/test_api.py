from fastapi.testclient import TestClient

from app.api.v1.dependencies import get_plan_agent
from app.main import app
from app.models.agent import AgentOutput
from app.models.travel import TravelResponse


class StubPlanAgent:
    async def run(self, request):  # noqa: ANN001
        result = TravelResponse.model_validate(
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
        return AgentOutput(
            request_id="req-test-001",
            result=result,
            fallback_used=False,
            latency_ms=12.3,
            agent_name="plan",
            provider_name="siliconflow",
        )

    async def generate_result(self, request):  # noqa: ANN001
        return (await self.run(request)).result


client = TestClient(app)


def override_plan_agent() -> StubPlanAgent:
    return StubPlanAgent()


app.dependency_overrides[get_plan_agent] = override_plan_agent


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


def test_agent_plan_success() -> None:
    response = client.post(
        "/api/v1/agent/plan",
        json={
            "origin": "上海",
            "destination": "杭州",
            "days": 2,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["request_id"] == "req-test-001"
    assert body["status"] == "completed"
    assert body["result"]["mode"] == "itinerary"
