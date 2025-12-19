from datetime import date, timedelta
from uuid import UUID
from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.crud import (
    get_or_create_work_week, get_work_week_by_date, get_work_weeks,
    get_work_items_by_week, create_work_item, update_work_item, delete_work_item,
    get_work_item
)
from app.schemas import WorkItemCreate, WorkItemUpdate
from app.models.work_item import TaskType, TaskStatus

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def parse_date(date_str: str) -> date:
    return date.fromisoformat(date_str)


@router.get("/input")
async def input_page(request: Request, db: Session = Depends(get_db)):
    today = date.today()
    current_week = get_or_create_work_week(db, today)
    return RedirectResponse(url=f"/input/{current_week.week_start}", status_code=302)


@router.get("/input/{week_start}")
async def input_page_for_week(request: Request, week_start: str, db: Session = Depends(get_db)):
    week_start_date = parse_date(week_start)
    week = get_or_create_work_week(db, week_start_date)
    items = get_work_items_by_week(db, week.id)
    
    # Get all weeks for dropdown
    all_weeks = get_work_weeks(db, limit=52)
    
    # Calculate points
    planned_points = sum(i.assigned_points for i in items if i.type == "PLANNED")
    unplanned_points = sum(i.assigned_points for i in items if i.type == "UNPLANNED")
    adhoc_points = sum(i.assigned_points for i in items if i.type == "ADHOC")
    total_used = planned_points + unplanned_points + adhoc_points
    
    # Previous/Next week navigation
    prev_week = week.week_start - timedelta(days=7)
    next_week = week.week_start + timedelta(days=7)
    
    return templates.TemplateResponse("input.html", {
        "request": request,
        "week": week,
        "items": items,
        "all_weeks": all_weeks,
        "planned_points": planned_points,
        "unplanned_points": unplanned_points,
        "adhoc_points": adhoc_points,
        "total_used": total_used,
        "remaining_points": 100 - total_used,
        "prev_week": prev_week,
        "next_week": next_week,
        "task_types": TaskType,
        "task_statuses": TaskStatus,
        "active_page": "input"
    })


@router.post("/api/work-items")
async def create_item(
    request: Request,
    week_id: UUID = Form(...),
    type: str = Form(...),
    title: str = Form(...),
    assigned_points: int = Form(...),
    start_date: Optional[str] = Form(None),
    end_date: Optional[str] = Form(None),
    planned_work: Optional[str] = Form(None),
    actual_work: Optional[str] = Form(None),
    next_week_plan: Optional[str] = Form(None),
    completion_points: Optional[int] = Form(None),
    status: str = Form("TODO"),
    db: Session = Depends(get_db)
):
    try:
        item_data = WorkItemCreate(
            week_id=week_id,
            type=TaskType(type),
            title=title,
            assigned_points=assigned_points,
            start_date=parse_date(start_date) if start_date else None,
            end_date=parse_date(end_date) if end_date else None,
            planned_work=planned_work or None,
            actual_work=actual_work or None,
            next_week_plan=next_week_plan or None,
            completion_points=completion_points,
            status=TaskStatus(status)
        )
        create_work_item(db, item_data)
        
        # Get week to redirect back
        week = db.query(WorkWeek).filter(WorkWeek.id == week_id).first()
        return RedirectResponse(url=f"/input/{week.week_start}", status_code=302)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/work-items/{item_id}")
async def update_item(
    item_id: UUID,
    type: str = Form(...),
    title: str = Form(...),
    assigned_points: int = Form(...),
    start_date: Optional[str] = Form(None),
    end_date: Optional[str] = Form(None),
    planned_work: Optional[str] = Form(None),
    actual_work: Optional[str] = Form(None),
    next_week_plan: Optional[str] = Form(None),
    completion_points: Optional[int] = Form(None),
    status: str = Form("TODO"),
    db: Session = Depends(get_db)
):
    try:
        item_data = WorkItemUpdate(
            type=TaskType(type),
            title=title,
            assigned_points=assigned_points,
            start_date=parse_date(start_date) if start_date else None,
            end_date=parse_date(end_date) if end_date else None,
            planned_work=planned_work or None,
            actual_work=actual_work or None,
            next_week_plan=next_week_plan or None,
            completion_points=completion_points,
            status=TaskStatus(status)
        )
        item = update_work_item(db, item_id, item_data)
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        
        return RedirectResponse(url=f"/input/{item.work_week.week_start}", status_code=302)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/work-items/{item_id}/delete")
async def delete_item(item_id: UUID, db: Session = Depends(get_db)):
    item = get_work_item(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    week_start = item.work_week.week_start
    delete_work_item(db, item_id)
    
    return RedirectResponse(url=f"/input/{week_start}", status_code=302)


from app.models.work_week import WorkWeek
