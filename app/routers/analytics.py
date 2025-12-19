from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.analytics import get_analytics_data
from app.middleware import get_current_week_stats
from app.auth import get_current_user_from_cookie

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/analytics")
async def analytics_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    data = get_analytics_data(db, weeks_back=12, user_id=user.id)
    sidebar_stats = get_current_week_stats(db, user.id)
    
    return templates.TemplateResponse("analytics.html", {
        "request": request,
        "user": user,
        "analytics": data,
        "active_page": "analytics",
        "sidebar_stats": sidebar_stats
    })


@router.get("/api/analytics/data")
async def analytics_data(weeks: int = 12, request: Request = None, db: Session = Depends(get_db)):
    user = get_current_user_from_cookie(request, db) if request else None
    user_id = user.id if user else None
    data = get_analytics_data(db, weeks_back=weeks, user_id=user_id)
    return JSONResponse(content=data)
