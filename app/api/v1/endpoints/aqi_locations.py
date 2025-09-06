from typing import List

from fastapi import APIRouter, HTTPException

from app.schemas.aqi_location import AqiLocationResponse
from app.services.aqi_data_service import AqiDataService

router = APIRouter()


@router.get("/", response_model=List[AqiLocationResponse])
async def get_all_locations():
    """
    Retrieve all AQI locations.
    
    Returns:
        List of all AQI locations with their metadata in JSON format
    """
    try:
        service = AqiDataService()
        locations = service.get_all_locations()
        return locations
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving locations: {str(e)}")