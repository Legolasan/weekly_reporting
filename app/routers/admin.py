from uuid import UUID
from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user_from_cookie
from app.crud.user import get_all_users_with_stats, delete_user, get_user
from app.middleware import get_current_week_stats

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/admin")
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    if not user.is_admin:
        return RedirectResponse(url="/", status_code=302)
    
    users = get_all_users_with_stats(db)
    
    # Get sidebar stats for current user
    sidebar_stats = get_current_week_stats(db, user.id)
    
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "user": user,
        "users": users,
        "active_page": "admin",
        "sidebar_stats": sidebar_stats,
        "success": request.query_params.get("success"),
        "error": request.query_params.get("error")
    })


@router.post("/admin/delete-user/{user_id}")
async def delete_user_handler(
    user_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    current_user = get_current_user_from_cookie(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)
    
    if not current_user.is_admin:
        return RedirectResponse(url="/", status_code=302)
    
    # Prevent admin from deleting themselves
    if str(current_user.id) == user_id:
        return RedirectResponse(url="/admin?error=Cannot+delete+your+own+account", status_code=302)
    
    # Get the user to delete
    user_to_delete = get_user(db, UUID(user_id))
    if not user_to_delete:
        return RedirectResponse(url="/admin?error=User+not+found", status_code=302)
    
    # Delete the user
    delete_user(db, UUID(user_id))
    
    return RedirectResponse(url="/admin?success=User+deleted+successfully", status_code=302)
