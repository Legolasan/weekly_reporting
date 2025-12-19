from fastapi import APIRouter, Depends, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user_from_cookie
from app.crud.user import verify_password, change_password, get_user_stats
from app.middleware import get_current_week_stats

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/profile")
async def profile_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    stats = get_user_stats(db, user.id)
    sidebar_stats = get_current_week_stats(db, user.id)
    
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "user": user,
        "stats": stats,
        "active_page": "profile",
        "sidebar_stats": sidebar_stats,
        "success": None,
        "error": None
    })


@router.post("/profile/change-password")
async def change_password_handler(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    stats = get_user_stats(db, user.id)
    sidebar_stats = get_current_week_stats(db, user.id)
    
    # Verify current password
    if not verify_password(current_password, user.password_hash):
        return templates.TemplateResponse("profile.html", {
            "request": request,
            "user": user,
            "stats": stats,
            "active_page": "profile",
            "sidebar_stats": sidebar_stats,
            "success": None,
            "error": "Current password is incorrect"
        })
    
    # Check new passwords match
    if new_password != confirm_password:
        return templates.TemplateResponse("profile.html", {
            "request": request,
            "user": user,
            "stats": stats,
            "active_page": "profile",
            "sidebar_stats": sidebar_stats,
            "success": None,
            "error": "New passwords do not match"
        })
    
    # Check password length
    if len(new_password) < 5:
        return templates.TemplateResponse("profile.html", {
            "request": request,
            "user": user,
            "stats": stats,
            "active_page": "profile",
            "sidebar_stats": sidebar_stats,
            "success": None,
            "error": "Password must be at least 5 characters"
        })
    
    # Change password
    change_password(db, user.id, new_password)
    
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "user": user,
        "stats": stats,
        "active_page": "profile",
        "sidebar_stats": sidebar_stats,
        "success": "Password changed successfully",
        "error": None
    })
