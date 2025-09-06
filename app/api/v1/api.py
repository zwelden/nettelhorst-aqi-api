from fastapi import APIRouter
from app.api.v1.endpoints import health, aqi_locations, aqi_history

api_router = APIRouter()

# Include routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(aqi_locations.router, prefix="/locations", tags=["locations"])
api_router.include_router(aqi_history.router, prefix="/history", tags=["history"])