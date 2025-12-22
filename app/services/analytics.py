from datetime import date, timedelta
from uuid import UUID
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.work_week import WorkWeek
from app.models.work_item import WorkItem, TaskType, TaskStatus


def get_analytics_data(db: Session, weeks_back: int = 12, user_id: Optional[UUID] = None) -> Dict[str, Any]:
    """Get analytics data for the specified number of weeks, optionally filtered by user."""
    end_date = date.today()
    start_date = end_date - timedelta(weeks=weeks_back)
    
    # Base query for weeks
    weeks_query = db.query(WorkWeek).filter(WorkWeek.week_start >= start_date)
    if user_id:
        weeks_query = weeks_query.filter(WorkWeek.user_id == user_id)
    weeks = weeks_query.order_by(WorkWeek.week_start).all()
    
    # Points trend data
    points_trend = []
    for week in weeks:
        items = db.query(WorkItem).filter(WorkItem.week_id == week.id).all()
        total_used = sum(item.assigned_points for item in items)
        total_points = week.total_points
        points_trend.append({
            "week": week.week_start.strftime("%m/%d"),
            "used": total_used,
            "remaining": total_points - total_used,
            "total_points": total_points,
            "ooo_days": week.ooo_days,
            "is_ooo": week.ooo_days > 0
        })
    
    # Task type distribution
    type_query = db.query(
        WorkItem.type,
        func.count(WorkItem.id).label("count"),
        func.sum(WorkItem.assigned_points).label("points")
    ).join(WorkWeek).filter(WorkWeek.week_start >= start_date)
    if user_id:
        type_query = type_query.filter(WorkWeek.user_id == user_id)
    type_counts = type_query.group_by(WorkItem.type).all()
    
    type_distribution = {t.value: {"count": 0, "points": 0} for t in TaskType}
    for row in type_counts:
        type_distribution[row.type] = {"count": row.count, "points": row.points or 0}
    
    # Status breakdown
    status_query = db.query(
        WorkItem.status,
        func.count(WorkItem.id).label("count")
    ).join(WorkWeek).filter(WorkWeek.week_start >= start_date)
    if user_id:
        status_query = status_query.filter(WorkWeek.user_id == user_id)
    status_counts = status_query.group_by(WorkItem.status).all()
    
    status_breakdown = {s.value: 0 for s in TaskStatus}
    for row in status_counts:
        status_breakdown[row.status] = row.count
    
    # Carry-over items (delayed/in-progress from past weeks)
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    
    carry_query = db.query(WorkItem).join(WorkWeek).filter(
        WorkItem.status.in_([TaskStatus.DELAYED.value, TaskStatus.IN_PROGRESS.value]),
        WorkWeek.week_end < monday
    )
    if user_id:
        carry_query = carry_query.filter(WorkWeek.user_id == user_id)
    carry_over = carry_query.all()
    
    carry_over_data = []
    for item in carry_over:
        weeks_old = (monday - item.work_week.week_start).days // 7
        carry_over_data.append({
            "id": str(item.id),
            "title": item.title,
            "type": item.type,
            "status": item.status,
            "points": item.assigned_points,
            "week": item.work_week.week_start.strftime("%Y-%m-%d"),
            "weeks_old": weeks_old
        })
    
    return {
        "points_trend": points_trend,
        "type_distribution": type_distribution,
        "status_breakdown": status_breakdown,
        "carry_over": carry_over_data
    }
