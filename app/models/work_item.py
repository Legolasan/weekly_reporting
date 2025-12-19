import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, Date, Integer, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class TaskType(str, Enum):
    PLANNED = "PLANNED"
    UNPLANNED = "UNPLANNED"
    ADHOC = "ADHOC"


class TaskStatus(str, Enum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    HOLD = "HOLD"
    DELAYED = "DELAYED"
    COMPLETED = "COMPLETED"
    ABANDONED = "ABANDONED"


class WorkItem(Base):
    __tablename__ = "work_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    week_id = Column(UUID(as_uuid=True), ForeignKey("work_weeks.id"), nullable=False)
    type = Column(String(20), nullable=False, default=TaskType.PLANNED.value)
    title = Column(String(255), nullable=False)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    assigned_points = Column(Integer, nullable=False, default=0)
    completion_points = Column(Integer, nullable=True)
    planned_work = Column(Text, nullable=True)
    actual_work = Column(Text, nullable=True)
    next_week_plan = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default=TaskStatus.TODO.value)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    work_week = relationship("WorkWeek", back_populates="work_items")
