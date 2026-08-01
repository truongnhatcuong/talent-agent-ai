from fastapi import APIRouter

from app.schemas.recruiter import MatchRequest
from app.services.recruiter_service import RecruiterService

router = APIRouter(
    prefix="/recruiter",
    tags=["Recruiter"]
)

service = RecruiterService()


@router.post("/match")
async def match(request: MatchRequest):

    result = await service.match_cv(
        request.cv,
        request.jd
    )

    return result