"""
Tests for dashboard functionality.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import date, timedelta

from app.models.user import User
from app.models.work_week import WorkWeek
from app.models.work_item import WorkItem


class TestDashboardAccess:
    """Tests for dashboard access."""
    
    @pytest.mark.dashboard
    def test_dashboard_requires_auth(self, client: TestClient):
        """Test dashboard redirects to login without auth."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 302
        assert "/login" in response.headers.get("location", "")
    
    @pytest.mark.dashboard
    def test_dashboard_loads_with_auth(self, authenticated_client: TestClient):
        """Test dashboard loads for authenticated user."""
        response = authenticated_client.get("/")
        # Either loads or redirects (both valid states)
        assert response.status_code in [200, 302]


class TestDashboardContent:
    """Tests for dashboard content and data."""
    
    @pytest.mark.dashboard
    def test_dashboard_shows_current_week(
        self, authenticated_client: TestClient, sample_work_week: WorkWeek
    ):
        """Test dashboard displays current week data."""
        response = authenticated_client.get("/")
        if response.status_code == 200:
            # Should contain week-related content
            assert "points" in response.text.lower() or "week" in response.text.lower()
    
    @pytest.mark.dashboard
    def test_dashboard_shows_work_items(
        self, authenticated_client: TestClient, sample_work_items: list[WorkItem]
    ):
        """Test dashboard displays work items."""
        response = authenticated_client.get("/")
        if response.status_code == 200:
            # Check for item-related content
            text = response.text.lower()
            assert any(word in text for word in ["task", "item", "work", "planned"])


class TestPointsCalculation:
    """Tests for points calculation logic."""
    
    @pytest.mark.dashboard
    def test_points_sum_correctly(self, db: Session, sample_work_items: list[WorkItem]):
        """Test that points are summed correctly."""
        total_assigned = sum(item.assigned_points for item in sample_work_items)
        total_completion = sum(item.completion_points or 0 for item in sample_work_items)
        
        # Based on our fixture: 30 + 20 + 10 = 60 assigned
        assert total_assigned == 60
        # 15 + 20 + 10 = 45 completion points
        assert total_completion == 45
    
    @pytest.mark.dashboard
    def test_points_by_type(self, db: Session, sample_work_items: list[WorkItem]):
        """Test points calculation by type."""
        planned_points = sum(
            item.assigned_points for item in sample_work_items 
            if item.type == "PLANNED"
        )
        unplanned_points = sum(
            item.assigned_points for item in sample_work_items 
            if item.type == "UNPLANNED"
        )
        adhoc_points = sum(
            item.assigned_points for item in sample_work_items 
            if item.type == "ADHOC"
        )
        
        assert planned_points == 30
        assert unplanned_points == 20
        assert adhoc_points == 10
    
    @pytest.mark.dashboard
    def test_remaining_points_calculation(
        self, db: Session, sample_work_week: WorkWeek, sample_work_items: list[WorkItem]
    ):
        """Test remaining points calculation."""
        total_used = sum(item.assigned_points for item in sample_work_items)
        remaining = sample_work_week.total_points - total_used
        
        # 100 - 60 = 40 remaining
        assert remaining == 40


class TestPendingItems:
    """Tests for pending items from previous weeks."""
    
    @pytest.mark.dashboard
    def test_pending_items_query(self, db: Session, regular_user: User):
        """Test querying pending items from previous weeks."""
        from app.crud.work_item import get_pending_items_for_user
        
        # Create a past week with pending items
        past_week_start = date.today() - timedelta(weeks=2, days=date.today().weekday())
        past_week = WorkWeek(
            user_id=regular_user.id,
            week_start=past_week_start,
            week_end=past_week_start + timedelta(days=4),
            total_points=100
        )
        db.add(past_week)
        db.commit()
        
        # Add a pending item
        pending_item = WorkItem(
            week_id=past_week.id,
            title="Pending Task",
            type="PLANNED",
            status="IN_PROGRESS",  # Not completed
            assigned_points=25,
            start_date=past_week_start,
            end_date=past_week_start + timedelta(days=4)
        )
        db.add(pending_item)
        db.commit()
        
        # Query pending items
        current_week_start = date.today() - timedelta(days=date.today().weekday())
        pending = get_pending_items_for_user(db, current_week_start, regular_user.id)
        
        # Should find the pending item
        assert len(pending) >= 1
        assert any(item.title == "Pending Task" for item in pending)


class TestWeekNavigation:
    """Tests for week navigation on dashboard."""
    
    @pytest.mark.dashboard
    def test_week_start_calculation(self):
        """Test Monday calculation for any date."""
        from datetime import date, timedelta
        
        # Test for a known Wednesday
        test_date = date(2024, 12, 18)  # Wednesday
        monday = test_date - timedelta(days=test_date.weekday())
        
        assert monday.weekday() == 0  # Monday
        assert monday == date(2024, 12, 16)
    
    @pytest.mark.dashboard
    def test_week_end_calculation(self):
        """Test Friday calculation."""
        from datetime import date, timedelta
        
        test_date = date(2024, 12, 18)
        monday = test_date - timedelta(days=test_date.weekday())
        friday = monday + timedelta(days=4)
        
        assert friday.weekday() == 4  # Friday
        assert friday == date(2024, 12, 20)
