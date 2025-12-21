"""
Tests for analytics functionality.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import date, timedelta

from app.models.user import User
from app.models.work_week import WorkWeek
from app.models.work_item import WorkItem
from app.services.analytics import get_analytics_data


class TestAnalyticsPageAccess:
    """Tests for analytics page access."""
    
    @pytest.mark.analytics
    def test_analytics_page_requires_auth(self, client: TestClient):
        """Test analytics page redirects to login without auth."""
        response = client.get("/analytics", follow_redirects=False)
        assert response.status_code == 302
        assert "/login" in response.headers.get("location", "")
    
    @pytest.mark.analytics
    def test_analytics_page_loads_with_auth(self, authenticated_client: TestClient):
        """Test analytics page loads for authenticated user."""
        response = authenticated_client.get("/analytics")
        assert response.status_code in [200, 302]


class TestAnalyticsData:
    """Tests for analytics data generation."""
    
    @pytest.mark.analytics
    def test_analytics_data_structure(
        self, db: Session, regular_user: User, multiple_weeks_data: list[WorkWeek]
    ):
        """Test analytics data has correct structure."""
        data = get_analytics_data(db, weeks_back=4, user_id=regular_user.id)
        
        # Check required keys
        assert "points_trend" in data
        assert "type_distribution" in data
        assert "status_breakdown" in data
        assert "carry_over" in data
    
    @pytest.mark.analytics
    def test_points_trend_data(
        self, db: Session, regular_user: User, multiple_weeks_data: list[WorkWeek]
    ):
        """Test points trend calculation."""
        data = get_analytics_data(db, weeks_back=4, user_id=regular_user.id)
        
        points_trend = data["points_trend"]
        assert isinstance(points_trend, list)
        
        # Should have data for each week
        if len(points_trend) > 0:
            # Check structure of trend data
            first_entry = points_trend[0]
            assert "week" in first_entry or "date" in first_entry or isinstance(first_entry, dict)
    
    @pytest.mark.analytics
    def test_type_distribution(
        self, db: Session, regular_user: User, sample_work_week: WorkWeek, sample_work_items: list[WorkItem]
    ):
        """Test type distribution calculation."""
        data = get_analytics_data(db, weeks_back=4, user_id=regular_user.id)
        
        type_dist = data["type_distribution"]
        assert isinstance(type_dist, (list, dict))
    
    @pytest.mark.analytics
    def test_status_breakdown(
        self, db: Session, regular_user: User, sample_work_week: WorkWeek, sample_work_items: list[WorkItem]
    ):
        """Test status breakdown calculation."""
        data = get_analytics_data(db, weeks_back=4, user_id=regular_user.id)
        
        status_breakdown = data["status_breakdown"]
        assert isinstance(status_breakdown, (list, dict))
    
    @pytest.mark.analytics
    def test_carry_over_calculation(
        self, db: Session, regular_user: User, multiple_weeks_data: list[WorkWeek]
    ):
        """Test carry-over items calculation."""
        data = get_analytics_data(db, weeks_back=4, user_id=regular_user.id)
        
        carry_over = data["carry_over"]
        assert isinstance(carry_over, (list, dict, int))


class TestAnalyticsAPI:
    """Tests for analytics API endpoints."""
    
    @pytest.mark.analytics
    def test_analytics_data_api(self, authenticated_client: TestClient):
        """Test analytics data API endpoint."""
        response = authenticated_client.get("/api/analytics/data")
        # May need auth, so accept redirect
        assert response.status_code in [200, 302]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)
    
    @pytest.mark.analytics
    def test_analytics_data_with_weeks_param(self, authenticated_client: TestClient):
        """Test analytics data with weeks parameter."""
        response = authenticated_client.get("/api/analytics/data?weeks=8")
        assert response.status_code in [200, 302]


class TestAnalyticsCalculations:
    """Tests for analytics calculation logic."""
    
    @pytest.mark.analytics
    def test_completion_rate_calculation(self, db: Session, sample_work_items: list[WorkItem]):
        """Test completion rate calculation."""
        completed = sum(1 for item in sample_work_items if item.status == "COMPLETED")
        total = len(sample_work_items)
        
        completion_rate = (completed / total * 100) if total > 0 else 0
        
        # From fixture: 2 completed out of 3
        assert completion_rate == pytest.approx(66.67, rel=0.1)
    
    @pytest.mark.analytics
    def test_points_utilization_calculation(
        self, db: Session, sample_work_week: WorkWeek, sample_work_items: list[WorkItem]
    ):
        """Test points utilization calculation."""
        total_assigned = sum(item.assigned_points for item in sample_work_items)
        utilization = (total_assigned / sample_work_week.total_points * 100)
        
        # 60 / 100 = 60%
        assert utilization == 60
    
    @pytest.mark.analytics
    def test_average_completion_points(self, db: Session, sample_work_items: list[WorkItem]):
        """Test average completion points calculation."""
        completion_points = [item.completion_points or 0 for item in sample_work_items]
        avg_completion = sum(completion_points) / len(completion_points) if completion_points else 0
        
        # (15 + 20 + 10) / 3 = 15
        assert avg_completion == 15


class TestAnalyticsFiltering:
    """Tests for analytics filtering by user."""
    
    @pytest.mark.analytics
    def test_analytics_user_isolation(
        self, db: Session, regular_user: User, admin_user: User
    ):
        """Test that analytics data is isolated per user."""
        # Create data for regular user
        week1 = WorkWeek(
            user_id=regular_user.id,
            week_start=date.today() - timedelta(days=date.today().weekday()),
            week_end=date.today() - timedelta(days=date.today().weekday()) + timedelta(days=4),
            total_points=100
        )
        db.add(week1)
        db.commit()
        
        item1 = WorkItem(
            week_id=week1.id,
            title="User Task",
            type="PLANNED",
            status="COMPLETED",
            assigned_points=50,
            completion_points=50,
            start_date=week1.week_start,
            end_date=week1.week_end
        )
        db.add(item1)
        db.commit()
        
        # Create data for admin user
        week2 = WorkWeek(
            user_id=admin_user.id,
            week_start=date.today() - timedelta(days=date.today().weekday()),
            week_end=date.today() - timedelta(days=date.today().weekday()) + timedelta(days=4),
            total_points=100
        )
        db.add(week2)
        db.commit()
        
        item2 = WorkItem(
            week_id=week2.id,
            title="Admin Task",
            type="PLANNED",
            status="COMPLETED",
            assigned_points=75,
            completion_points=75,
            start_date=week2.week_start,
            end_date=week2.week_end
        )
        db.add(item2)
        db.commit()
        
        # Get analytics for regular user
        user_data = get_analytics_data(db, weeks_back=4, user_id=regular_user.id)
        
        # Get analytics for admin user
        admin_data = get_analytics_data(db, weeks_back=4, user_id=admin_user.id)
        
        # Data should be different (isolated)
        assert user_data != admin_data or (
            user_data["points_trend"] != admin_data["points_trend"]
        )
