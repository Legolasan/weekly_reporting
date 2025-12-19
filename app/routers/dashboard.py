from datetime import date, timedelta
from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.crud import get_or_create_work_week, get_work_items_by_week, get_pending_items

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
async def dashboard(request: Request, db: Session = Depends(get_db)):
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    
    # Get current week
    current_week = get_or_create_work_week(db, today)
    items = get_work_items_by_week(db, current_week.id)
    
    # Calculate points breakdown
    planned_points = sum(i.assigned_points for i in items if i.type == "PLANNED")
    unplanned_points = sum(i.assigned_points for i in items if i.type == "UNPLANNED")
    adhoc_points = sum(i.assigned_points for i in items if i.type == "ADHOC")
    total_used = planned_points + unplanned_points + adhoc_points
    
    # Get pending items from previous weeks
    pending_items = get_pending_items(db, monday)
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "current_week": current_week,
        "items": items,
        "planned_points": planned_points,
        "unplanned_points": unplanned_points,
        "adhoc_points": adhoc_points,
        "total_used": total_used,
        "remaining_points": 100 - total_used,
        "pending_items": pending_items,
        "active_page": "dashboard"
    })
