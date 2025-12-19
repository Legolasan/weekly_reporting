from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.analytics import get_analytics_data
from app.middleware import get_current_week_stats

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/analytics")
async def analytics_page(request: Request, db: Session = Depends(get_db)):
    data = get_analytics_data(db, weeks_back=12)
    sidebar_stats = get_current_week_stats(db)
    
    return templates.TemplateResponse("analytics.html", {
        "request": request,
        "analytics": data,
        "active_page": "analytics",
        "sidebar_stats": sidebar_stats
    })


@router.get("/api/analytics/data")
async def analytics_data(weeks: int = 12, db: Session = Depends(get_db)):
    data = get_analytics_data(db, weeks_back=weeks)
    return JSONResponse(content=data)
