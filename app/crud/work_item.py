from datetime import date
from uuid import UUID
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.work_item import WorkItem, TaskStatus
from app.schemas.work_item import WorkItemCreate, WorkItemUpdate


def get_work_item(db: Session, item_id: UUID) -> Optional[WorkItem]:
    return db.query(WorkItem).filter(WorkItem.id == item_id).first()


def get_work_items_by_week(db: Session, week_id: UUID) -> List[WorkItem]:
    return db.query(WorkItem).filter(WorkItem.week_id == week_id).order_by(WorkItem.created_at).all()


def validate_points(db: Session, week_id: UUID, new_points: int, exclude_item_id: UUID = None) -> int:
    """Validate points and return remaining points. Raises ValueError if exceeded."""
    query = db.query(func.coalesce(func.sum(WorkItem.assigned_points), 0)).filter(WorkItem.week_id == week_id)
    if exclude_item_id:
        query = query.filter(WorkItem.id != exclude_item_id)
    current = query.scalar()
    remaining = 100 - current
    if new_points > remaining:
        raise ValueError(f"Only {remaining} points remaining for this week")
    return remaining


def create_work_item(db: Session, item: WorkItemCreate) -> WorkItem:
    validate_points(db, item.week_id, item.assigned_points)
    db_item = WorkItem(
        week_id=item.week_id,
        type=item.type.value,
        title=item.title,
        start_date=item.start_date,
        end_date=item.end_date,
        assigned_points=item.assigned_points,
        completion_points=item.completion_points,
        planned_work=item.planned_work,
        actual_work=item.actual_work,
        next_week_plan=item.next_week_plan,
        document_url=item.document_url,
        status=item.status.value
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def update_work_item(db: Session, item_id: UUID, item: WorkItemUpdate) -> Optional[WorkItem]:
    db_item = get_work_item(db, item_id)
    if not db_item:
        return None
    
    update_data = item.model_dump(exclude_unset=True)
    
    if "assigned_points" in update_data:
        validate_points(db, db_item.week_id, update_data["assigned_points"], exclude_item_id=item_id)
    
    for field, value in update_data.items():
        if field in ("type", "status") and value is not None:
            value = value.value
        setattr(db_item, field, value)
    
    db.commit()
    db.refresh(db_item)
    return db_item


def delete_work_item(db: Session, item_id: UUID) -> bool:
    db_item = get_work_item(db, item_id)
    if not db_item:
        return False
    db.delete(db_item)
    db.commit()
    return True


def get_pending_items(db: Session, before_date: date) -> List[WorkItem]:
    """Get items that are delayed or in progress from previous weeks."""
    return db.query(WorkItem).join(WorkItem.work_week).filter(
        WorkItem.status.in_([TaskStatus.DELAYED.value, TaskStatus.IN_PROGRESS.value, TaskStatus.TODO.value]),
        WorkItem.work_week.has(WorkWeek.week_end < before_date)
    ).order_by(WorkItem.created_at.desc()).all()


def get_pending_items_for_user(db: Session, before_date: date, user_id: UUID) -> List[WorkItem]:
    """Get items that are delayed or in progress from previous weeks for a specific user."""
    from app.models.work_week import WorkWeek
    return db.query(WorkItem).join(WorkItem.work_week).filter(
        WorkItem.status.in_([TaskStatus.DELAYED.value, TaskStatus.IN_PROGRESS.value, TaskStatus.TODO.value]),
        WorkWeek.week_end < before_date,
        WorkWeek.user_id == user_id
    ).order_by(WorkItem.created_at.desc()).all()


from app.models.work_week import WorkWeek
