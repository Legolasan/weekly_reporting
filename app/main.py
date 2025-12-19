from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from app.routers import dashboard_router, input_router, analytics_router, reports_router

app = FastAPI(title="Work Tracker", description="Weekly work tracking with points system")


# Health check endpoint - must be before other routes
@app.get("/health")
async def health_check():
    return JSONResponse(content={"status": "healthy"}, status_code=200)


# Startup event - create tables
@app.on_event("startup")
async def startup_event():
    try:
        from app.database import engine, Base
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully")
    except Exception as e:
        print(f"Database initialization error: {e}")


# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include routers
app.include_router(dashboard_router)
app.include_router(input_router)
app.include_router(analytics_router)
app.include_router(reports_router)
