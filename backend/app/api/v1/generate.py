from fastapi import APIRouter, Depends

from app.api.v1.dependencies import get_travel_service
from app.schemas.travel import TravelRequest, TravelResponse
from app.services.travel_service import TravelService

router = APIRouter()


@router.post("/generate", response_model=TravelResponse)
async def generate_plan(
    request: TravelRequest,
    travel_service: TravelService = Depends(get_travel_service),
) -> TravelResponse:
    return await travel_service.generate_plan(request)
