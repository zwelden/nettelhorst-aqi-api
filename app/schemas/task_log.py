from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class TaskLogBase(BaseModel):
    task_name: str
    status: str
    error_message: Optional[str] = None
    result: Optional[str] = None
    is_successful: bool = False


class TaskLogCreate(TaskLogBase):
    pass


class TaskLogUpdate(BaseModel):
    status: Optional[str] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result: Optional[str] = None
    is_successful: Optional[bool] = None


class TaskLogResponse(TaskLogBase):
    id: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True