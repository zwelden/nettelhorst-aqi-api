from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .aqi_location import AqiLocationResponse


class Aqi30MinuteHistoryBase(BaseModel):
    measure_time: datetime
    aqi_location_id: int
    measure_data: Dict[str, Any]


class Aqi30MinuteHistoryCreate(Aqi30MinuteHistoryBase):
    pass


class Aqi30MinuteHistoryUpdate(BaseModel):
    measure_time: Optional[datetime] = None
    aqi_location_id: Optional[int] = None
    measure_data: Optional[Dict[str, Any]] = None


class Aqi30MinuteHistoryResponse(Aqi30MinuteHistoryBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class Aqi30MinuteHistoryWithLocation(Aqi30MinuteHistoryResponse):
    location: Optional["AqiLocationResponse"] = None
    
    class Config:
        from_attributes = True