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
    from app.database import engine, Base
    from sqlalchemy import text, inspect
    import bcrypt
    
    # Step 1: Create tables
    try:
        Base.metadata.create_all(bind=engine, checkfirst=True)
        print("Database tables ready")
    except Exception as e:
        print(f"Table creation note: {e}")
    
    # Step 2: Ensure work_weeks has user_id column (migration fix)
    try:
        with engine.connect() as conn:
            inspector = inspect(engine)
            columns = [col['name'] for col in inspector.get_columns('work_weeks')]
            
            if 'user_id' not in columns:
                print("Adding user_id column to work_weeks...")
                conn.execute(text("ALTER TABLE work_weeks ADD COLUMN user_id UUID"))
                conn.commit()
                print("Added user_id column to work_weeks")
    except Exception as e:
        print(f"Schema update note: {e}")
    
    # Step 2b: Fix unique constraint on work_weeks for multi-user support
    try:
        with engine.connect() as conn:
            # Check if the old unique index exists and drop it
            result = conn.execute(text("""
                SELECT indexname FROM pg_indexes 
                WHERE tablename = 'work_weeks' AND indexname = 'ix_work_weeks_week_start'
            """))
            index_exists = result.fetchone()
            
            if index_exists:
                # Check if it's unique
                result = conn.execute(text("""
                    SELECT indisunique FROM pg_index 
                    JOIN pg_class ON pg_index.indexrelid = pg_class.oid
                    WHERE pg_class.relname = 'ix_work_weeks_week_start'
                """))
                is_unique = result.fetchone()
                
                if is_unique and is_unique[0]:
                    print("Dropping old unique index on week_start...")
                    conn.execute(text("DROP INDEX ix_work_weeks_week_start"))
                    conn.execute(text("CREATE INDEX ix_work_weeks_week_start ON work_weeks(week_start)"))
                    conn.commit()
                    print("Fixed work_weeks index for multi-user support")
            
            # Create the user_id + week_start unique constraint if it doesn't exist
            result = conn.execute(text("""
                SELECT constraint_name FROM information_schema.table_constraints 
                WHERE table_name = 'work_weeks' AND constraint_name = 'uq_user_week'
            """))
            constraint_exists = result.fetchone()
            
            if not constraint_exists:
                try:
                    conn.execute(text("ALTER TABLE work_weeks ADD CONSTRAINT uq_user_week UNIQUE (user_id, week_start)"))
                    conn.commit()
                    print("Added unique constraint on (user_id, week_start)")
                except Exception as ce:
                    print(f"Constraint note: {ce}")
    except Exception as e:
        print(f"Index fix note: {e}")
    
    # Step 3: Ensure admin user exists
    try:
        from app.models.user import User
        
        db = SessionLocal()
        try:
            admin_email = "arun.sunderraj@hevodata.com"
            admin = db.query(User).filter(User.email == admin_email).first()
            
            if not admin:
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
