from datetime import date, timedelta
from uuid import UUID
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


def get_current_week_stats(db, user_id: UUID = None):
    """Get current week's points statistics for a user."""
    from app.models.work_week import WorkWeek
    from app.models.work_item import WorkItem
    
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    
    # Build query with user filter
    query = db.query(WorkWeek).filter(WorkWeek.week_start == monday)
    if user_id:
        query = query.filter(WorkWeek.user_id == user_id)
    
    week = query.first()
    
    if not week:
        return {
            "week_start": monday,
            "week_end": monday + timedelta(days=4),
            "total_used": 0,
            "remaining": 100,
            "total_points": 100,
            "percentage": 0,
            "planned": 0,
            "unplanned": 0,
            "adhoc": 0
        }
    
    items = db.query(WorkItem).filter(WorkItem.week_id == week.id).all()
    
    planned = sum(i.assigned_points for i in items if i.type == "PLANNED")
    unplanned = sum(i.assigned_points for i in items if i.type == "UNPLANNED")
    adhoc = sum(i.assigned_points for i in items if i.type == "ADHOC")
    total_used = planned + unplanned + adhoc
    total_points = week.total_points
    
    return {
        "week_start": week.week_start,
        "week_end": week.week_end,
        "total_used": total_used,
        "remaining": total_points - total_used,
        "total_points": total_points,
        "percentage": (total_used / total_points * 100) if total_points > 0 else 0,
        "planned": planned,
        "unplanned": unplanned,
        "adhoc": adhoc
    }
