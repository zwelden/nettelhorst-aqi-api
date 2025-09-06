from fastapi import APIRouter
from app.schemas.health import HealthResponse

router = APIRouter()


@router.get("/", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Basic health check endpoint
    """
    return HealthResponse(
        status="healthy",
        service="FastAPI Backend",
        version="1.0.0"
    )