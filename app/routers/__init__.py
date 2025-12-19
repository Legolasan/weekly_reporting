from app.routers.dashboard import router as dashboard_router
from app.routers.input import router as input_router
from app.routers.analytics import router as analytics_router
from app.routers.reports import router as reports_router

__all__ = ["dashboard_router", "input_router", "analytics_router", "reports_router"]
