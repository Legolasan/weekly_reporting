from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from fastapi import Request, HTTPException, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.config import get_settings

settings = get_settings()

# Secret key for signing sessions
SECRET_KEY = settings.database_url[:32] if len(settings.database_url) >= 32 else "work-tracker-secret-key-change-me"
SESSION_COOKIE_NAME = "work_tracker_session"
SESSION_MAX_AGE = 60 * 60 * 24 * 7  # 7 days in seconds

serializer = URLSafeTimedSerializer(SECRET_KEY)


def create_session_token(user_id: UUID) -> str:
    """Create a signed session token for the user."""
    return serializer.dumps(str(user_id))


def verify_session_token(token: str) -> Optional[str]:
    """Verify and decode a session token. Returns user_id or None."""
    try:
        user_id = serializer.loads(token, max_age=SESSION_MAX_AGE)
        return user_id
    except (BadSignature, SignatureExpired):
        return None


def get_current_user_from_cookie(request: Request, db: Session) -> Optional[User]:
    """Get the current user from the session cookie."""
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        return None
    
    user_id = verify_session_token(token)
    if not user_id:
        return None
    
    try:
        user = db.query(User).filter(User.id == UUID(user_id)).first()
        return user
    except:
        return None


def set_session_cookie(response: RedirectResponse, user_id: UUID) -> RedirectResponse:
    """Set the session cookie on the response."""
    token = create_session_token(user_id)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=SESSION_MAX_AGE,
        httponly=True,
        samesite="lax"
    )
    return response


def clear_session_cookie(response: RedirectResponse) -> RedirectResponse:
    """Clear the session cookie."""
    response.delete_cookie(key=SESSION_COOKIE_NAME)
    return response


# Public routes that don't require authentication
PUBLIC_ROUTES = ["/login", "/signup", "/health", "/static"]


def is_public_route(path: str) -> bool:
    """Check if a route is public (doesn't require auth)."""
    for route in PUBLIC_ROUTES:
        if path.startswith(route):
            return True
    return False


def require_auth(request: Request, db: Session = Depends(get_db)) -> User:
    """Dependency that requires authentication."""
    user = get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


def require_admin(request: Request, db: Session = Depends(get_db)) -> User:
    """Dependency that requires admin authentication."""
    user = get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
