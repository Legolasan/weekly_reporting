from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Request, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.export import export_to_csv, export_to_excel, get_filtered_items
from app.models.work_item import TaskType, TaskStatus
from app.crud import get_work_weeks

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def parse_date_optional(date_str: Optional[str]) -> Optional[date]:
    if date_str:
        return date.fromisoformat(date_str)
    return None


@router.get("/reports")
async def reports_page(
    request: Request,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    task_type: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    items = get_filtered_items(
        db,
        parse_date_optional(start_date),
        parse_date_optional(end_date),
        task_type,
        status
    )
    
    # Calculate summary stats
    total_points = sum(item["Assigned Points"] for item in items)
    type_counts = {}
    status_counts = {}
    for item in items:
        type_counts[item["Type"]] = type_counts.get(item["Type"], 0) + 1
        status_counts[item["Status"]] = status_counts.get(item["Status"], 0) + 1
    
    all_weeks = get_work_weeks(db, limit=52)
    
    return templates.TemplateResponse("reports.html", {
        "request": request,
        "items": items,
        "total_items": len(items),
        "total_points": total_points,
        "type_counts": type_counts,
        "status_counts": status_counts,
        "all_weeks": all_weeks,
        "task_types": TaskType,
        "task_statuses": TaskStatus,
        "filters": {
            "start_date": start_date,
            "end_date": end_date,
            "task_type": task_type,
            "status": status
        },
        "active_page": "reports"
    })


@router.get("/reports/export/csv")
async def export_csv(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    task_type: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    csv_data = export_to_csv(
        db,
        parse_date_optional(start_date),
        parse_date_optional(end_date),
        task_type,
        status
    )
    
    filename = f"work_tracker_export_{date.today().strftime('%Y%m%d')}.csv"
    
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/reports/export/excel")
async def export_excel(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    task_type: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    excel_data = export_to_excel(
        db,
        parse_date_optional(start_date),
        parse_date_optional(end_date),
        task_type,
        status
    )
    
    filename = f"work_tracker_export_{date.today().strftime('%Y%m%d')}.xlsx"
    
    return Response(
        content=excel_data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
