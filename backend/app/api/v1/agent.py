from fastapi import APIRouter, Depends

from app.api.v1.dependencies import get_plan_agent
from app.models.agent import AgentPlanResponse
from app.models.travel import TravelRequest
from app.agents.plan_agent import PlanAgent

router = APIRouter(prefix="/agent")


@router.post("/plan", response_model=AgentPlanResponse)
async def agent_plan(
    request: TravelRequest,
    plan_agent: PlanAgent = Depends(get_plan_agent),
) -> AgentPlanResponse:
    output = await plan_agent.run(request)
    return AgentPlanResponse(
        request_id=output.request_id,
        status=output.status,
        result=output.result,
    )
