from datetime import date, timedelta
from uuid import UUID
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.work_week import WorkWeek


def get_work_week(db: Session, week_id: UUID) -> Optional[WorkWeek]:
    return db.query(WorkWeek).filter(WorkWeek.id == week_id).first()


def get_work_week_by_date(db: Session, week_start: date) -> Optional[WorkWeek]:
    return db.query(WorkWeek).filter(WorkWeek.week_start == week_start).first()


def get_work_weeks(db: Session, skip: int = 0, limit: int = 100) -> List[WorkWeek]:
    return db.query(WorkWeek).order_by(WorkWeek.week_start.desc()).offset(skip).limit(limit).all()


def create_work_week(db: Session, week_start: date, week_end: date) -> WorkWeek:
    db_week = WorkWeek(week_start=week_start, week_end=week_end)
    db.add(db_week)
    db.commit()
    db.refresh(db_week)
    return db_week


def get_or_create_work_week(db: Session, target_date: date) -> WorkWeek:
    """Get or create a work week for the given date."""
    monday = target_date - timedelta(days=target_date.weekday())
    friday = monday + timedelta(days=4)
    
    week = get_work_week_by_date(db, monday)
    if not week:
        week = create_work_week(db, monday, friday)
    return week
