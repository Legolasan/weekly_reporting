from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.routers import dashboard_router, input_router, analytics_router, reports_router
from app.routers.auth import router as auth_router
from app.routers.profile import router as profile_router
from app.routers.admin import router as admin_router
from app.auth import get_current_user_from_cookie, is_public_route
from app.database import SessionLocal

app = FastAPI(title="Work Tracker", description="Weekly work tracking with points system")


# Authentication Middleware
class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip auth for public routes
        if is_public_route(request.url.path):
            return await call_next(request)
        
        # Check for valid session
        db = SessionLocal()
        try:
            user = get_current_user_from_cookie(request, db)
            if not user:
                return RedirectResponse(url="/login", status_code=302)
            # Store user in request state for later use
            request.state.user = user
        finally:
            db.close()
        
        return await call_next(request)


# Add middleware
app.add_middleware(AuthMiddleware)


# Health check endpoint - must be before other routes
@app.get("/health")
async def health_check():
    return JSONResponse(content={"status": "healthy"}, status_code=200)


# Startup event - create tables and ensure admin user exists
@app.on_event("startup")
async def startup_event():
    try:
        from app.database import engine, Base
        # checkfirst=True prevents errors if tables already exist
        Base.metadata.create_all(bind=engine, checkfirst=True)
        print("Database tables ready")
        
        # Ensure admin user exists
        from app.crud.user import get_user_by_email, create_user
        db = SessionLocal()
        try:
            admin_email = "arun.sunderraj@hevodata.com"
            admin = get_user_by_email(db, admin_email)
            if not admin:
                from app.models.user import User
                from passlib.context import CryptContext
                pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
                
                admin_user = User(
                    email=admin_email,
                    password_hash=pwd_context.hash("12345"),
                    is_admin=True
                )
                db.add(admin_user)
                db.commit()
                print(f"Created admin user: {admin_email}")
            else:
                print(f"Admin user exists: {admin_email}")
        finally:
            db.close()
    except Exception as e:
        # Don't crash if tables exist or other DB issues
        print(f"Database note: {e}")


# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include routers - auth first (public routes)
app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(input_router)
app.include_router(analytics_router)
app.include_router(reports_router)
app.include_router(profile_router)
app.include_router(admin_router)
