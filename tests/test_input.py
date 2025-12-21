"""
Tests for work item input functionality.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import date, timedelta
from uuid import uuid4

from app.models.user import User
from app.models.work_week import WorkWeek
from app.models.work_item import WorkItem
from app.crud.work_item import (
    create_work_item, get_work_item, update_work_item, 
    delete_work_item, get_work_items_by_week
)


class TestInputPageAccess:
    """Tests for input page access."""
    
    @pytest.mark.input
    def test_input_page_requires_auth(self, client: TestClient):
        """Test input page redirects to login without auth."""
        response = client.get("/input", follow_redirects=False)
        assert response.status_code == 302
        assert "/login" in response.headers.get("location", "")
    
    @pytest.mark.input
    def test_input_page_loads_with_auth(self, authenticated_client: TestClient):
        """Test input page loads for authenticated user."""
        response = authenticated_client.get("/input")
        assert response.status_code in [200, 302]
    
    @pytest.mark.input
    def test_input_page_with_week_param(
        self, authenticated_client: TestClient, sample_work_week: WorkWeek
    ):
        """Test input page with specific week."""
        week_start = sample_work_week.week_start.isoformat()
        response = authenticated_client.get(f"/input/{week_start}")
        assert response.status_code in [200, 302]


class TestWorkItemCRUD:
    """Tests for work item CRUD operations."""
    
    @pytest.mark.input
    def test_create_work_item(self, db: Session, sample_work_week: WorkWeek):
        """Test creating a work item."""
        from app.schemas.work_item import WorkItemCreate
        
        item_data = WorkItemCreate(
            week_id=sample_work_week.id,
            title="New Task",
            type="PLANNED",
            status="TODO",
            assigned_points=25,
            start_date=sample_work_week.week_start,
            end_date=sample_work_week.week_end,
            planned_work="Plan the work",
            actual_work=None,
            next_week_plan=None
        )
        
        item = create_work_item(db, item_data)
        
        assert item is not None
        assert item.title == "New Task"
        assert item.type == "PLANNED"
        assert item.assigned_points == 25
    
    @pytest.mark.input
    def test_get_work_item(self, db: Session, sample_work_items: list[WorkItem]):
        """Test retrieving a work item."""
        item = sample_work_items[0]
        retrieved = get_work_item(db, item.id)
        
        assert retrieved is not None
        assert retrieved.id == item.id
        assert retrieved.title == item.title
    
    @pytest.mark.input
    def test_update_work_item(self, db: Session, sample_work_items: list[WorkItem]):
        """Test updating a work item."""
        from app.schemas.work_item import WorkItemUpdate
        
        item = sample_work_items[0]
        update_data = WorkItemUpdate(
            title="Updated Title",
            status="COMPLETED",
            completion_points=30
        )
        
        updated = update_work_item(db, item.id, update_data)
        
        assert updated is not None
        assert updated.title == "Updated Title"
        assert updated.status == "COMPLETED"
        assert updated.completion_points == 30
    
    @pytest.mark.input
    def test_delete_work_item(self, db: Session, sample_work_week: WorkWeek):
        """Test deleting a work item."""
        from app.schemas.work_item import WorkItemCreate
        
        # Create an item to delete
        item_data = WorkItemCreate(
            week_id=sample_work_week.id,
            title="To Delete",
            type="ADHOC",
            status="TODO",
            assigned_points=5,
            start_date=sample_work_week.week_start,
            end_date=sample_work_week.week_end
        )
        item = create_work_item(db, item_data)
        item_id = item.id
        
        # Delete it
        result = delete_work_item(db, item_id)
        assert result is True
        
        # Verify it's gone
        deleted = get_work_item(db, item_id)
        assert deleted is None
    
    @pytest.mark.input
    def test_get_items_by_week(self, db: Session, sample_work_week: WorkWeek, sample_work_items: list[WorkItem]):
        """Test getting all items for a week."""
        items = get_work_items_by_week(db, sample_work_week.id)
        
        assert len(items) == len(sample_work_items)


class TestWorkItemValidation:
    """Tests for work item validation."""
    
    @pytest.mark.input
    def test_item_types(self, db: Session, sample_work_week: WorkWeek):
        """Test valid item types."""
        from app.schemas.work_item import WorkItemCreate
        
        for item_type in ["PLANNED", "UNPLANNED", "ADHOC"]:
            item_data = WorkItemCreate(
                week_id=sample_work_week.id,
                title=f"{item_type} Task",
                type=item_type,
                status="TODO",
                assigned_points=10,
                start_date=sample_work_week.week_start,
                end_date=sample_work_week.week_end
            )
            item = create_work_item(db, item_data)
            assert item.type == item_type
    
    @pytest.mark.input
    def test_item_statuses(self, db: Session, sample_work_week: WorkWeek):
        """Test valid item statuses."""
        from app.schemas.work_item import WorkItemCreate
        
        statuses = ["TODO", "IN_PROGRESS", "HOLD", "DELAYED", "COMPLETED", "ABANDONED"]
        
        for status in statuses:
            item_data = WorkItemCreate(
                week_id=sample_work_week.id,
                title=f"{status} Task",
                type="PLANNED",
                status=status,
                assigned_points=10,
                start_date=sample_work_week.week_start,
                end_date=sample_work_week.week_end
            )
            item = create_work_item(db, item_data)
            assert item.status == status
    
    @pytest.mark.input
    def test_points_range(self, db: Session, sample_work_week: WorkWeek):
        """Test points are within valid range."""
        from app.schemas.work_item import WorkItemCreate
        
        # Valid points
        item_data = WorkItemCreate(
            week_id=sample_work_week.id,
            title="Valid Points Task",
            type="PLANNED",
            status="TODO",
            assigned_points=50,
            start_date=sample_work_week.week_start,
            end_date=sample_work_week.week_end
        )
        item = create_work_item(db, item_data)
        assert item.assigned_points == 50


class TestWorkItemAPI:
    """Tests for work item API endpoints."""
    
    @pytest.mark.input
    def test_create_item_api(
        self, authenticated_client: TestClient, sample_work_week: WorkWeek
    ):
        """Test creating item via API."""
        response = authenticated_client.post(
            "/api/work-items",
            data={
                "week_id": str(sample_work_week.id),
                "title": "API Created Task",
                "type": "PLANNED",
                "status": "TODO",
                "assigned_points": "20",
                "start_date": sample_work_week.week_start.isoformat(),
                "end_date": sample_work_week.week_end.isoformat(),
                "planned_work": "Test work"
            },
            follow_redirects=False
        )
        # Should succeed or redirect
        assert response.status_code in [200, 302, 303]
    
    @pytest.mark.input
    def test_update_item_api(
        self, authenticated_client: TestClient, sample_work_items: list[WorkItem]
    ):
        """Test updating item via API."""
        item = sample_work_items[0]
        response = authenticated_client.post(
            f"/api/work-items/{item.id}",
            data={
                "title": "Updated via API",
                "type": item.type,
                "status": "COMPLETED",
                "assigned_points": str(item.assigned_points),
                "completion_points": str(item.assigned_points),
                "start_date": item.start_date.isoformat(),
                "end_date": item.end_date.isoformat()
            },
            follow_redirects=False
        )
        assert response.status_code in [200, 302, 303]
    
    @pytest.mark.input
    def test_delete_item_api(
        self, authenticated_client: TestClient, db: Session, sample_work_week: WorkWeek
    ):
        """Test deleting item via API."""
        from app.schemas.work_item import WorkItemCreate
        
        # Create an item to delete
        item_data = WorkItemCreate(
            week_id=sample_work_week.id,
            title="To Delete via API",
            type="ADHOC",
            status="TODO",
            assigned_points=5,
            start_date=sample_work_week.week_start,
            end_date=sample_work_week.week_end
        )
        item = create_work_item(db, item_data)
        
        response = authenticated_client.post(
            f"/api/work-items/{item.id}/delete",
            follow_redirects=False
        )
        assert response.status_code in [200, 302, 303]


class TestFutureWeekPlanning:
    """Tests for future week planning mode."""
    
    @pytest.mark.input
    def test_future_week_detection(self):
        """Test detecting if a week is in the future."""
        today = date.today()
        current_monday = today - timedelta(days=today.weekday())
        next_monday = current_monday + timedelta(weeks=1)
        
        # Current week is not future
        assert current_monday <= today
        
        # Next week is future
        assert next_monday > today
    
    @pytest.mark.input
    def test_create_future_week_item(self, db: Session, regular_user: User):
        """Test creating item for future week."""
        from app.schemas.work_item import WorkItemCreate
        from app.crud.work_week import create_work_week
        
        # Create a future week
        today = date.today()
        next_monday = today - timedelta(days=today.weekday()) + timedelta(weeks=1)
        next_friday = next_monday + timedelta(days=4)
        
        future_week = create_work_week(db, next_monday, next_friday, regular_user.id)
        
        # Create item for future week (planning mode)
        item_data = WorkItemCreate(
            week_id=future_week.id,
            title="Future Task",
            type="PLANNED",
            status="TODO",
            assigned_points=30,
            start_date=next_monday,
            end_date=next_friday,
            planned_work="Plan for next week"
        )
        item = create_work_item(db, item_data)
        
        assert item is not None
        assert item.title == "Future Task"
        # Completion points should be None/0 for future items
        assert item.completion_points is None or item.completion_points == 0
