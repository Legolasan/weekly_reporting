from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.crud.user import get_user_by_email, create_user, authenticate_user
from app.auth import set_session_cookie, clear_session_cookie, get_current_user_from_cookie

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/login")
async def login_page(request: Request, db: Session = Depends(get_db)):
    # If already logged in, redirect to dashboard
    user = get_current_user_from_cookie(request, db)
    if user:
        return RedirectResponse(url="/", status_code=302)
    
    return templates.TemplateResponse("login.html", {
        "request": request,
        "error": None
    })


@router.post("/login")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, email, password)
    
    if not user:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Invalid email or password"
        })
    
    response = RedirectResponse(url="/", status_code=302)
    return set_session_cookie(response, user.id)


@router.get("/signup")
async def signup_page(request: Request, db: Session = Depends(get_db)):
    # If already logged in, redirect to dashboard
    user = get_current_user_from_cookie(request, db)
    if user:
        return RedirectResponse(url="/", status_code=302)
    
    return templates.TemplateResponse("signup.html", {
        "request": request,
        "error": None
    })


@router.post("/signup")
async def signup(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    # Validate passwords match
    if password != confirm_password:
        return templates.TemplateResponse("signup.html", {
            "request": request,
            "error": "Passwords do not match"
        })
    
    # Validate password length
    if len(password) < 5:
        return templates.TemplateResponse("signup.html", {
            "request": request,
            "error": "Password must be at least 5 characters"
        })
    
    # Check if user already exists
    existing_user = get_user_by_email(db, email)
    if existing_user:
        return templates.TemplateResponse("signup.html", {
            "request": request,
            "error": "An account with this email already exists"
        })
    
    # Create new user
    user = create_user(db, email, password)
    
    # Log them in
    response = RedirectResponse(url="/", status_code=302)
    return set_session_cookie(response, user.id)


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=302)
    return clear_session_cookie(response)
