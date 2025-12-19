import uuid
from datetime import datetime
from sqlalchemy import Column, String, Date, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class WorkWeek(Base):
    __tablename__ = "work_weeks"
    __table_args__ = (
        UniqueConstraint('user_id', 'week_start', name='uq_user_week'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    week_start = Column(Date, nullable=False, index=True)
    week_end = Column(Date, nullable=False)
    total_points = Column(Integer, default=100)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="work_weeks")
    work_items = relationship("WorkItem", back_populates="work_week", cascade="all, delete-orphan")

    @property
    def used_points(self):
        return sum(item.assigned_points for item in self.work_items)

    @property
    def remaining_points(self):
        return self.total_points - self.used_points
