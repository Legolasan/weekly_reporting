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
    # Step 1: Create tables
    try:
        from app.database import engine, Base
        Base.metadata.create_all(bind=engine, checkfirst=True)
        print("Database tables ready")
    except Exception as e:
        print(f"Table creation note: {e}")
    
    # Step 2: Ensure admin user exists (separate try block)
    try:
        from app.models.user import User
        import bcrypt
        
        db = SessionLocal()
        try:
            admin_email = "arun.sunderraj@hevodata.com"
            admin = db.query(User).filter(User.email == admin_email).first()
            
            if not admin:
                # Hash password using bcrypt directly (avoiding passlib compatibility issues)
                password_hash = bcrypt.hashpw("12345".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                
                admin_user = User(
                    email=admin_email,
                    password_hash=password_hash,
                    is_admin=True
                )
                db.add(admin_user)
                db.commit()
                print(f"Created admin user: {admin_email}")
            else:
                print(f"Admin user exists: {admin_email}")
        except Exception as inner_e:
            print(f"Admin user creation error: {inner_e}")
            db.rollback()
        finally:
            db.close()
    except Exception as e:
        print(f"Startup user check error: {e}")


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
