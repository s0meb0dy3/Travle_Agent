from fastapi import APIRouter, Depends

from app.agents.plan_agent import PlanAgent
from app.api.v1.dependencies import get_plan_agent
from app.models.travel import TravelRequest, TravelResponse

router = APIRouter()


@router.post("/generate", response_model=TravelResponse)
async def generate_plan(
    request: TravelRequest,
    plan_agent: PlanAgent = Depends(get_plan_agent),
) -> TravelResponse:
    return await plan_agent.generate_result(request)
