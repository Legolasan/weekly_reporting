from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routers import dashboard_router, input_router, analytics_router, reports_router
from app.database import engine, Base

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Work Tracker", description="Weekly work tracking with points system")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include routers
app.include_router(dashboard_router)
app.include_router(input_router)
app.include_router(analytics_router)
app.include_router(reports_router)
