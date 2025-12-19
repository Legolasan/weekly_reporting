from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from app.routers import dashboard_router, input_router, analytics_router, reports_router

app = FastAPI(title="Work Tracker", description="Weekly work tracking with points system")


# Health check endpoint - must be before other routes
@app.get("/health")
async def health_check():
    return JSONResponse(content={"status": "healthy"}, status_code=200)


# Startup event - create tables (only if they don't exist)
@app.on_event("startup")
async def startup_event():
    try:
        from app.database import engine, Base
        # checkfirst=True prevents errors if tables already exist
        Base.metadata.create_all(bind=engine, checkfirst=True)
        print("Database tables ready")
    except Exception as e:
        # Don't crash if tables exist or other DB issues
        print(f"Database note: {e}")


# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include routers
app.include_router(dashboard_router)
app.include_router(input_router)
app.include_router(analytics_router)
app.include_router(reports_router)
