from datetime import date, datetime
from uuid import UUID
from typing import Optional, List
from pydantic import BaseModel


class WorkWeekBase(BaseModel):
    week_start: date
    week_end: date
    total_points: int = 100


class WorkWeekCreate(WorkWeekBase):
    pass


class WorkWeekUpdate(BaseModel):
    total_points: Optional[int] = None


class WorkWeekResponse(WorkWeekBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    used_points: int = 0
    remaining_points: int = 100

    class Config:
        from_attributes = True
