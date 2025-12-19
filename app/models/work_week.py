import uuid
from datetime import datetime
from sqlalchemy import Column, String, Date, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class WorkWeek(Base):
    __tablename__ = "work_weeks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    week_start = Column(Date, nullable=False, unique=True, index=True)
    week_end = Column(Date, nullable=False)
    total_points = Column(Integer, default=100)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    work_items = relationship("WorkItem", back_populates="work_week", cascade="all, delete-orphan")

    @property
    def used_points(self):
        return sum(item.assigned_points for item in self.work_items)

    @property
    def remaining_points(self):
        return self.total_points - self.used_points
