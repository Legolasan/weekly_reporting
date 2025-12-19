from uuid import UUID
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from passlib.context import CryptContext
from app.models.user import User
from app.models.work_week import WorkWeek
from app.models.work_item import WorkItem

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_user(db: Session, user_id: UUID) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    return db.query(User).order_by(User.created_at.desc()).offset(skip).limit(limit).all()


def create_user(db: Session, email: str, password: str, is_admin: bool = False) -> User:
    hashed = hash_password(password)
    db_user = User(email=email, password_hash=hashed, is_admin=is_admin)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def change_password(db: Session, user_id: UUID, new_password: str) -> bool:
    user = get_user(db, user_id)
    if not user:
        return False
    user.password_hash = hash_password(new_password)
    db.commit()
    return True


def delete_user(db: Session, user_id: UUID) -> bool:
    user = get_user(db, user_id)
    if not user:
        return False
    db.delete(user)
    db.commit()
    return True


def get_user_stats(db: Session, user_id: UUID) -> dict:
    """Get statistics for a user."""
    weeks = db.query(WorkWeek).filter(WorkWeek.user_id == user_id).all()
    total_weeks = len(weeks)
    
    total_items = 0
    total_points = 0
    for week in weeks:
        items = db.query(WorkItem).filter(WorkItem.week_id == week.id).all()
        total_items += len(items)
        total_points += sum(item.assigned_points for item in items)
    
    return {
        "total_weeks": total_weeks,
        "total_items": total_items,
        "total_points": total_points
    }


def get_all_users_with_stats(db: Session) -> List[dict]:
    """Get all users with their statistics for admin view."""
    users = get_users(db)
    result = []
    for user in users:
        stats = get_user_stats(db, user.id)
        result.append({
            "id": str(user.id),
            "email": user.email,
            "is_admin": user.is_admin,
            "created_at": user.created_at,
            **stats
        })
    return result
