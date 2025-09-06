from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any


class Aqi5MinuteHistoryBase(BaseModel):
    measure_time: datetime
    aqi_location_id: int
    measure_data: Dict[str, Any]


class Aqi5MinuteHistoryCreate(Aqi5MinuteHistoryBase):
    pass


class Aqi5MinuteHistoryUpdate(BaseModel):
    measure_time: Optional[datetime] = None
    aqi_location_id: Optional[int] = None
    measure_data: Optional[Dict[str, Any]] = None


class Aqi5MinuteHistoryResponse(Aqi5MinuteHistoryBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class Aqi5MinuteHistoryWithLocation(Aqi5MinuteHistoryResponse):
    from typing import TYPE_CHECKING
    if TYPE_CHECKING:
        from .aqi_location import AqiLocationResponse
    
    location: Optional["AqiLocationResponse"] = None
    
    class Config:
        from_attributes = True