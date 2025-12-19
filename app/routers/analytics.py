from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.analytics import get_analytics_data

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/analytics")
async def analytics_page(request: Request, db: Session = Depends(get_db)):
    data = get_analytics_data(db, weeks_back=12)
    
    return templates.TemplateResponse("analytics.html", {
        "request": request,
        "analytics": data,
        "active_page": "analytics"
    })


@router.get("/api/analytics/data")
async def analytics_data(weeks: int = 12, db: Session = Depends(get_db)):
    data = get_analytics_data(db, weeks_back=weeks)
    return JSONResponse(content=data)
