from datetime import date, timedelta
from uuid import UUID
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.work_week import WorkWeek


def get_work_week(db: Session, week_id: UUID, user_id: UUID = None) -> Optional[WorkWeek]:
    query = db.query(WorkWeek).filter(WorkWeek.id == week_id)
    if user_id:
        query = query.filter(WorkWeek.user_id == user_id)
    return query.first()


def get_work_week_by_date(db: Session, week_start: date, user_id: UUID) -> Optional[WorkWeek]:
    return db.query(WorkWeek).filter(
        WorkWeek.week_start == week_start,
        WorkWeek.user_id == user_id
    ).first()


def get_work_weeks(db: Session, user_id: UUID, skip: int = 0, limit: int = 100) -> List[WorkWeek]:
    return db.query(WorkWeek).filter(
        WorkWeek.user_id == user_id
    ).order_by(WorkWeek.week_start.desc()).offset(skip).limit(limit).all()


def get_all_work_weeks(db: Session, skip: int = 0, limit: int = 100) -> List[WorkWeek]:
    """Get all work weeks (for admin)."""
    return db.query(WorkWeek).order_by(WorkWeek.week_start.desc()).offset(skip).limit(limit).all()


def create_work_week(db: Session, week_start: date, week_end: date, user_id: UUID, ooo_days: int = 0) -> WorkWeek:
    """Create a work week with calculated total_points based on OOO days."""
    db_week = WorkWeek(week_start=week_start, week_end=week_end, user_id=user_id, ooo_days=ooo_days)
    db_week.total_points = db_week.calculate_total_points()
    db.add(db_week)
    db.commit()
    db.refresh(db_week)
    return db_week


def update_work_week_ooo(db: Session, week_id: UUID, ooo_days: int, user_id: UUID = None) -> Optional[WorkWeek]:
    """Update OOO days for a work week and recalculate total_points.
    
    Args:
        db: Database session
        week_id: The week to update
        ooo_days: Number of OOO days (0-5)
        user_id: Optional user_id to verify ownership
    
    Returns:
        Updated WorkWeek or None if not found
    """
    if ooo_days < 0 or ooo_days > 5:
        raise ValueError("OOO days must be between 0 and 5")
    
    week = get_work_week(db, week_id, user_id)
    if not week:
        return None
    
    week.ooo_days = ooo_days
    week.total_points = week.calculate_total_points()
    db.commit()
    db.refresh(week)
    return week


def get_or_create_work_week(db: Session, target_date: date, user_id: UUID) -> WorkWeek:
    """Get or create a work week for the given date and user.
    
    Handles race conditions by catching IntegrityError on duplicate inserts.
    """
    from sqlalchemy.exc import IntegrityError
    
    monday = target_date - timedelta(days=target_date.weekday())
    friday = monday + timedelta(days=4)
    
    # First, try to get existing week
    week = get_work_week_by_date(db, monday, user_id)
    if week:
        return week
    
    # If not found, try to create (with race condition handling)
    try:
        week = create_work_week(db, monday, friday, user_id)
        return week
    except IntegrityError:
        # Another request created it concurrently, rollback and fetch
        db.rollback()
        week = get_work_week_by_date(db, monday, user_id)
        return week
