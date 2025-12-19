from datetime import date, datetime
from uuid import UUID
from typing import Optional
from pydantic import BaseModel
from app.models.work_item import TaskType, TaskStatus


class WorkItemBase(BaseModel):
    type: TaskType = TaskType.PLANNED
    title: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    assigned_points: int = 0
    completion_points: Optional[int] = None
    planned_work: Optional[str] = None
    actual_work: Optional[str] = None
    next_week_plan: Optional[str] = None
    status: TaskStatus = TaskStatus.TODO


class WorkItemCreate(WorkItemBase):
    week_id: UUID


class WorkItemUpdate(BaseModel):
    type: Optional[TaskType] = None
    title: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    assigned_points: Optional[int] = None
    completion_points: Optional[int] = None
    planned_work: Optional[str] = None
    actual_work: Optional[str] = None
    next_week_plan: Optional[str] = None
    status: Optional[TaskStatus] = None


class WorkItemResponse(WorkItemBase):
    id: UUID
    week_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
