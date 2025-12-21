"""
Shared test fixtures for Work Tracker tests.
"""
import os
import pytest
from datetime import date, timedelta
from typing import Generator
from uuid import uuid4

# Set test environment before importing app modules
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.user import User
from app.models.work_week import WorkWeek
from app.models.work_item import WorkItem
from app.crud.user import hash_password


# Test database setup - SQLite in-memory for speed
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for tests."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """Create a fresh database for each test."""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """Create a test client with database override."""
    import app.database as app_database
    import app.main as app_main
    
    # Override dependency injection
    app.dependency_overrides[get_db] = override_get_db
    
    # Also patch SessionLocal used by middleware directly
    original_session_local = app_database.SessionLocal
    app_database.SessionLocal = TestingSessionLocal
    app_main.SessionLocal = TestingSessionLocal
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Restore
    app_database.SessionLocal = original_session_local
    app_main.SessionLocal = original_session_local
    app.dependency_overrides.clear()


@pytest.fixture
def admin_user(db: Session) -> User:
    """Create an admin user for testing."""
    user = User(
        id=uuid4(),
        email="admin@test.com",
        password_hash=hash_password("admin123"),
        is_admin=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def regular_user(db: Session) -> User:
    """Create a regular user for testing."""
    user = User(
        id=uuid4(),
        email="user@test.com",
        password_hash=hash_password("user123"),
        is_admin=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def authenticated_client(client: TestClient, regular_user: User) -> TestClient:
    """Create a client with authenticated session."""
    response = client.post(
        "/login",
        data={"email": "user@test.com", "password": "user123"},
        follow_redirects=False
    )
    # TestClient automatically handles cookies
    return client


@pytest.fixture
def admin_client(client: TestClient, admin_user: User) -> TestClient:
    """Create a client with admin authenticated session."""
    response = client.post(
        "/login",
        data={"email": "admin@test.com", "password": "admin123"},
        follow_redirects=False
    )
    # TestClient automatically handles cookies
    return client


@pytest.fixture
def sample_work_week(db: Session, regular_user: User) -> WorkWeek:
    """Create a sample work week for testing."""
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    friday = monday + timedelta(days=4)
    
    week = WorkWeek(
        id=uuid4(),
        user_id=regular_user.id,
        week_start=monday,
        week_end=friday,
        total_points=100
    )
    db.add(week)
    db.commit()
    db.refresh(week)
    return week


@pytest.fixture
def sample_work_items(db: Session, sample_work_week: WorkWeek) -> list[WorkItem]:
    """Create sample work items for testing."""
    items = [
        WorkItem(
            id=uuid4(),
            week_id=sample_work_week.id,
            title="Planned Task 1",
            type="PLANNED",
            status="IN_PROGRESS",
            assigned_points=30,
            completion_points=15,
            start_date=sample_work_week.week_start,
            end_date=sample_work_week.week_end,
            planned_work="Complete feature X",
            actual_work="Working on feature X",
            next_week_plan="Finish and test"
        ),
        WorkItem(
            id=uuid4(),
            week_id=sample_work_week.id,
            title="Unplanned Task",
            type="UNPLANNED",
            status="COMPLETED",
            assigned_points=20,
            completion_points=20,
            start_date=sample_work_week.week_start,
            end_date=sample_work_week.week_start + timedelta(days=1),
            planned_work="Handle urgent bug",
            actual_work="Fixed production issue",
            next_week_plan=None
        ),
        WorkItem(
            id=uuid4(),
            week_id=sample_work_week.id,
            title="Ad-hoc Meeting",
            type="ADHOC",
            status="COMPLETED",
            assigned_points=10,
            completion_points=10,
            start_date=sample_work_week.week_start + timedelta(days=2),
            end_date=sample_work_week.week_start + timedelta(days=2),
            planned_work=None,
            actual_work="Team sync meeting",
            next_week_plan=None
        )
    ]
    
    for item in items:
        db.add(item)
    db.commit()
    
    for item in items:
        db.refresh(item)
    
    return items


@pytest.fixture
def multiple_weeks_data(db: Session, regular_user: User) -> list[WorkWeek]:
    """Create multiple weeks with items for analytics testing."""
    weeks = []
    today = date.today()
    
    for i in range(4):  # Create 4 weeks of data
        week_start = today - timedelta(weeks=i, days=today.weekday())
        week_end = week_start + timedelta(days=4)
        
        week = WorkWeek(
            id=uuid4(),
            user_id=regular_user.id,
            week_start=week_start,
            week_end=week_end,
            total_points=100
        )
        db.add(week)
        db.commit()
        db.refresh(week)
        
        # Add items to each week
        item = WorkItem(
            id=uuid4(),
            week_id=week.id,
            title=f"Task for week {i}",
            type=["PLANNED", "UNPLANNED", "ADHOC"][i % 3],
            status=["COMPLETED", "IN_PROGRESS", "TO_DO"][i % 3],
            assigned_points=25,
            completion_points=20 if i % 2 == 0 else 0,
            start_date=week_start,
            end_date=week_end
        )
        db.add(item)
        db.commit()
        
        weeks.append(week)
    
    return weeks
