from datetime import date, timedelta
from uuid import UUID
from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional
from collections import OrderedDict
import time
from app.database import get_db
from app.crud import (
    get_or_create_work_week, get_work_week_by_date, get_work_weeks,
    get_work_items_by_week, create_work_item, update_work_item, delete_work_item,
    get_work_item
)
from app.crud.work_week import update_work_week_ooo
from app.schemas import WorkItemCreate, WorkItemUpdate
from app.models.work_item import TaskType, TaskStatus
from app.middleware import get_current_week_stats
from app.auth import get_current_user_from_cookie

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Simple idempotency cache with TTL (5 minutes)
# Stores: {idempotency_key: (timestamp, redirect_url)}
_idempotency_cache: OrderedDict = OrderedDict()
_IDEMPOTENCY_TTL = 300  # 5 minutes

def check_idempotency(key: str) -> Optional[str]:
    """Check if request is duplicate. Returns redirect URL if duplicate, None otherwise."""
    if not key:
        return None
    
    # Clean expired entries
    now = time.time()
    while _idempotency_cache:
        oldest_key, (ts, _) = next(iter(_idempotency_cache.items()))
        if now - ts > _IDEMPOTENCY_TTL:
            _idempotency_cache.pop(oldest_key)
        else:
            break
    
    # Check if key exists
    if key in _idempotency_cache:
        _, redirect_url = _idempotency_cache[key]
        return redirect_url
    
    return None

def store_idempotency(key: str, redirect_url: str):
    """Store idempotency key with result."""
    if key:
        _idempotency_cache[key] = (time.time(), redirect_url)


def parse_date(date_str: str) -> date:
    return date.fromisoformat(date_str)


@router.get("/input")
async def input_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    today = date.today()
    current_week = get_or_create_work_week(db, today, user.id)
    return RedirectResponse(url=f"/input/{current_week.week_start}", status_code=302)


@router.get("/input/{week_start}")
async def input_page_for_week(request: Request, week_start: str, db: Session = Depends(get_db)):
    user = get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    week_start_date = parse_date(week_start)
    week = get_or_create_work_week(db, week_start_date, user.id)
    items = get_work_items_by_week(db, week.id)
    
    # Get all weeks for dropdown (for this user)
    all_weeks = get_work_weeks(db, user.id, limit=52)
    
    # Calculate points
    planned_points = sum(i.assigned_points for i in items if i.type == "PLANNED")
    unplanned_points = sum(i.assigned_points for i in items if i.type == "UNPLANNED")
    adhoc_points = sum(i.assigned_points for i in items if i.type == "ADHOC")
    total_used = planned_points + unplanned_points + adhoc_points
    
    # Previous/Next week navigation
    prev_week = week.week_start - timedelta(days=7)
    next_week = week.week_start + timedelta(days=7)
    
    # Convert items to JSON-serializable format for JavaScript
    items_json = [
        {
            "id": str(item.id),
            "type": item.type,
            "title": item.title,
            "start_date": item.start_date.isoformat() if item.start_date else None,
            "end_date": item.end_date.isoformat() if item.end_date else None,
            "assigned_points": item.assigned_points,
            "completion_points": item.completion_points,
            "planned_work": item.planned_work,
            "actual_work": item.actual_work,
            "next_week_plan": item.next_week_plan,
            "document_url": item.document_url,
            "status": item.status
        }
        for item in items
    ]
    
    # Get sidebar stats
    sidebar_stats = get_current_week_stats(db, user.id)
    
    # Detect if this is a future week (for planning mode)
    today = date.today()
    is_future_week = week.week_start > today
    
    return templates.TemplateResponse("input.html", {
        "request": request,
        "user": user,
        "week": week,
        "items": items,
        "items_json": items_json,
        "all_weeks": all_weeks,
        "planned_points": planned_points,
        "unplanned_points": unplanned_points,
        "adhoc_points": adhoc_points,
        "total_used": total_used,
        "remaining_points": week.total_points - total_used,
        "prev_week": prev_week,
        "next_week": next_week,
        "task_types": TaskType,
        "task_statuses": TaskStatus,
        "active_page": "input",
        "sidebar_stats": sidebar_stats,
        "is_future_week": is_future_week
    })


def parse_int_or_none(value) -> Optional[int]:
    """Parse integer from form, return None for empty strings."""
    if value is None or value == "" or value == "None":
        return None
    return int(value)


@router.post("/api/work-items")
async def create_item(
    request: Request,
    week_id: UUID = Form(...),
    type: str = Form(...),
    title: str = Form(...),
    assigned_points: str = Form(...),
    start_date: Optional[str] = Form(None),
    end_date: Optional[str] = Form(None),
    planned_work: Optional[str] = Form(None),
    actual_work: Optional[str] = Form(None),
    next_week_plan: Optional[str] = Form(None),
    document_url: Optional[str] = Form(None),
    completion_points: Optional[str] = Form(None),
    status: str = Form("TODO"),
    idempotency_key: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    user = get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    # Check for duplicate submission
    cached_redirect = check_idempotency(idempotency_key)
    if cached_redirect:
        return RedirectResponse(url=cached_redirect, status_code=302)
    
    try:
        item_data = WorkItemCreate(
            week_id=week_id,
            type=TaskType(type),
            title=title,
            assigned_points=int(assigned_points) if assigned_points else 0,
            start_date=parse_date(start_date) if start_date else None,
            end_date=parse_date(end_date) if end_date else None,
            planned_work=planned_work or None,
            actual_work=actual_work or None,
            next_week_plan=next_week_plan or None,
            document_url=document_url or None,
            completion_points=parse_int_or_none(completion_points),
            status=TaskStatus(status)
        )
        create_work_item(db, item_data)
        
        # Get week to redirect back
        week = db.query(WorkWeek).filter(WorkWeek.id == week_id).first()
        redirect_url = f"/input/{week.week_start}"
        
        # Store idempotency key
        store_idempotency(idempotency_key, redirect_url)
        
        return RedirectResponse(url=redirect_url, status_code=302)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/work-items/{item_id}")
async def update_item(
    item_id: UUID,
    request: Request,
    type: str = Form(...),
    title: str = Form(...),
    assigned_points: str = Form(...),
    start_date: Optional[str] = Form(None),
    end_date: Optional[str] = Form(None),
    planned_work: Optional[str] = Form(None),
    actual_work: Optional[str] = Form(None),
    next_week_plan: Optional[str] = Form(None),
    document_url: Optional[str] = Form(None),
    completion_points: Optional[str] = Form(None),
    status: str = Form("TODO"),
    idempotency_key: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    user = get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    # Check for duplicate submission
    cached_redirect = check_idempotency(idempotency_key)
    if cached_redirect:
        return RedirectResponse(url=cached_redirect, status_code=302)
    
    try:
        item_data = WorkItemUpdate(
            type=TaskType(type),
            title=title,
            assigned_points=int(assigned_points) if assigned_points else 0,
            start_date=parse_date(start_date) if start_date else None,
            end_date=parse_date(end_date) if end_date else None,
            planned_work=planned_work or None,
            actual_work=actual_work or None,
            next_week_plan=next_week_plan or None,
            document_url=document_url or None,
            completion_points=parse_int_or_none(completion_points),
            status=TaskStatus(status)
        )
        item = update_work_item(db, item_id, item_data)
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        
        redirect_url = f"/input/{item.work_week.week_start}"
        
        # Store idempotency key
        store_idempotency(idempotency_key, redirect_url)
        
        return RedirectResponse(url=redirect_url, status_code=302)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/work-items/{item_id}/delete")
async def delete_item(item_id: UUID, request: Request, db: Session = Depends(get_db)):
    user = get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    item = get_work_item(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    week_start = item.work_week.week_start
    delete_work_item(db, item_id)
    
    return RedirectResponse(url=f"/input/{week_start}", status_code=302)


@router.post("/api/work-weeks/{week_id}/ooo")
async def update_week_ooo(
    week_id: UUID,
    request: Request,
    ooo_days: int = Form(...),
    db: Session = Depends(get_db)
):
    """Update OOO days for a work week and recalculate total_points."""
    user = get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    # Validate ooo_days range
    if ooo_days < 0 or ooo_days > 5:
        raise HTTPException(status_code=400, detail="OOO days must be between 0 and 5")
    
    # Get the week to check ownership and current items
    from app.crud.work_week import get_work_week
    week = get_work_week(db, week_id, user.id)
    if not week:
        raise HTTPException(status_code=404, detail="Work week not found")
    
    # Calculate new total_points
    new_total_points = (5 - ooo_days) * 20
    
    # Check if existing work items exceed new capacity
    items = get_work_items_by_week(db, week_id)
    current_points = sum(item.assigned_points for item in items)
    
    if current_points > new_total_points:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot set {ooo_days} OOO days. Current work items total {current_points} points, but only {new_total_points} points available."
        )
    
    # Update OOO days
    updated_week = update_work_week_ooo(db, week_id, ooo_days, user.id)
    if not updated_week:
        raise HTTPException(status_code=500, detail="Failed to update OOO days")
    
    return RedirectResponse(url=f"/input/{updated_week.week_start}", status_code=302)


from app.models.work_week import WorkWeek
