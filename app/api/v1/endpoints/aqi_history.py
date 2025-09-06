from typing import List
from fastapi import APIRouter, HTTPException, Query

from app.schemas.aqi_5_minute_history import Aqi5MinuteHistoryResponse
from app.services.aqi_data_service import AqiDataService

router = APIRouter()


@router.get("/{location_id}/hours", response_model=List[Aqi5MinuteHistoryResponse])
async def get_history_by_hours(
    location_id: int,
    hours: int = Query(default=24, ge=1, le=168, description="Number of hours to retrieve data for (1-168)")
):
    """
    Retrieve AQI history data for the past N hours for a specific location.
    
    Args:
        location_id: The external location ID
        hours: Number of hours to retrieve data for (default 24, max 168 = 1 week)
    
    Returns:
        List of AQI measurement records sorted by measure_time descending (most recent first)
    """
    try:
        service = AqiDataService()
        history_records = service.get_history_by_hours(location_id, hours)
        return history_records
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving history data: {str(e)}")


@router.get("/{location_id}/days", response_model=List[Aqi5MinuteHistoryResponse])
async def get_history_by_days(
    location_id: int,
    days: int = Query(ge=1, le=365, description="Number of days to retrieve data for (1-365)")
):
    """
    Retrieve AQI history data for the past N days for a specific location.
    
    Args:
        location_id: The external location ID
        days: Number of days to retrieve data for (max 365)
    
    Returns:
        List of AQI measurement records sorted by measure_time descending (most recent first)
    """
    try:
        service = AqiDataService()
        history_records = service.get_history_by_days(location_id, days)
        return history_records
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving history data: {str(e)}")