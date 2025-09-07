from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .aqi_5_minute_history import Aqi5MinuteHistoryResponse
    from .aqi_30_minute_history import Aqi30MinuteHistoryResponse


class AqiLocationBase(BaseModel):
    location_id: int
    location_name: str
    location_description: str
    serial_no: str
    model: str
    firmware_version: str


class AqiLocationCreate(AqiLocationBase):
    pass


class AqiLocationUpdate(BaseModel):
    location_id: Optional[int] = None
    location_name: Optional[str] = None
    location_description: Optional[str] = None
    serial_no: Optional[str] = None
    model: Optional[str] = None
    firmware_version: Optional[str] = None


class AqiLocationResponse(AqiLocationBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AqiLocationWithHistory(AqiLocationResponse):
    history_records: List["Aqi5MinuteHistoryResponse"] = []
    
    class Config:
        from_attributes = True


class AqiLocationWith30MinuteHistory(AqiLocationResponse):
    thirty_minute_history_records: List["Aqi30MinuteHistoryResponse"] = []
    
    class Config:
        from_attributes = True


class AqiLocationWithAllHistory(AqiLocationResponse):
    history_records: List["Aqi5MinuteHistoryResponse"] = []
    thirty_minute_history_records: List["Aqi30MinuteHistoryResponse"] = []
    
    class Config:
        from_attributes = True