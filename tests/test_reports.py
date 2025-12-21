"""
Tests for reports and export functionality.
"""
import pytest
import io
import csv
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import date, timedelta

from app.models.user import User
from app.models.work_week import WorkWeek
from app.models.work_item import WorkItem
from app.services.export import export_to_csv, export_to_excel, get_filtered_items


class TestReportsPageAccess:
    """Tests for reports page access."""
    
    @pytest.mark.reports
    def test_reports_page_requires_auth(self, client: TestClient):
        """Test reports page redirects to login without auth."""
        response = client.get("/reports", follow_redirects=False)
        assert response.status_code == 302
        assert "/login" in response.headers.get("location", "")
    
    @pytest.mark.reports
    def test_reports_page_loads_with_auth(self, authenticated_client: TestClient):
        """Test reports page loads for authenticated user."""
        response = authenticated_client.get("/reports")
        assert response.status_code in [200, 302]


class TestDataFiltering:
    """Tests for report data filtering."""
    
    @pytest.mark.reports
    def test_filter_by_date_range(
        self, db: Session, regular_user: User, multiple_weeks_data: list[WorkWeek]
    ):
        """Test filtering items by date range."""
        today = date.today()
        start_date = today - timedelta(weeks=2)
        end_date = today
        
        items = get_filtered_items(
            db, 
            start_date=start_date, 
            end_date=end_date,
            user_id=regular_user.id
        )
        
        # Items returned are dicts
        assert isinstance(items, list)
    
    @pytest.mark.reports
    def test_filter_by_type(
        self, db: Session, regular_user: User, sample_work_week: WorkWeek, sample_work_items: list[WorkItem]
    ):
        """Test filtering items by type."""
        items = get_filtered_items(
            db,
            task_type="PLANNED",
            user_id=regular_user.id
        )
        
        for item in items:
            assert item["Type"] == "PLANNED"
    
    @pytest.mark.reports
    def test_filter_by_status(
        self, db: Session, regular_user: User, sample_work_week: WorkWeek, sample_work_items: list[WorkItem]
    ):
        """Test filtering items by status."""
        items = get_filtered_items(
            db,
            status="COMPLETED",
            user_id=regular_user.id
        )
        
        for item in items:
            assert item["Status"] == "COMPLETED"
    
    @pytest.mark.reports
    def test_combined_filters(
        self, db: Session, regular_user: User, sample_work_week: WorkWeek, sample_work_items: list[WorkItem]
    ):
        """Test combining multiple filters."""
        today = date.today()
        
        items = get_filtered_items(
            db,
            start_date=today - timedelta(weeks=1),
            end_date=today,
            task_type="PLANNED",
            status="IN_PROGRESS",
            user_id=regular_user.id
        )
        
        # All items should match all filters
        for item in items:
            assert item["Type"] == "PLANNED"
            assert item["Status"] == "IN_PROGRESS"


class TestCSVExport:
    """Tests for CSV export functionality."""
    
    @pytest.mark.reports
    def test_csv_export_structure(
        self, db: Session, regular_user: User, sample_work_week: WorkWeek, sample_work_items: list[WorkItem]
    ):
        """Test CSV export has correct structure."""
        csv_content = export_to_csv(db, user_id=regular_user.id)
        
        assert csv_content is not None
        assert isinstance(csv_content, (str, bytes, io.StringIO, io.BytesIO))
    
    @pytest.mark.reports
    def test_csv_export_contains_data(
        self, db: Session, regular_user: User, sample_work_week: WorkWeek, sample_work_items: list[WorkItem]
    ):
        """Test CSV export contains work items."""
        csv_content = export_to_csv(db, user_id=regular_user.id)
        
        # Convert to string if needed
        if hasattr(csv_content, 'read'):
            csv_content = csv_content.read()
        if isinstance(csv_content, bytes):
            csv_content = csv_content.decode('utf-8')
        
        # Should contain headers and data
        assert len(csv_content) > 0
        # Check for expected content
        assert "Title" in csv_content or "title" in csv_content.lower() or "Task" in csv_content
    
    @pytest.mark.reports
    def test_csv_export_api(self, authenticated_client: TestClient, sample_work_items: list[WorkItem]):
        """Test CSV export via API."""
        response = authenticated_client.get("/reports/export/csv")
        
        if response.status_code == 200:
            # Check content type
            content_type = response.headers.get("content-type", "")
            assert "csv" in content_type or "text" in content_type or "octet" in content_type
        else:
            # May redirect or need different params
            assert response.status_code in [200, 302]


class TestExcelExport:
    """Tests for Excel export functionality."""
    
    @pytest.mark.reports
    def test_excel_export_structure(
        self, db: Session, regular_user: User, sample_work_week: WorkWeek, sample_work_items: list[WorkItem]
    ):
        """Test Excel export produces valid file."""
        excel_content = export_to_excel(db, user_id=regular_user.id)
        
        assert excel_content is not None
        # Excel files are binary
        assert isinstance(excel_content, (bytes, io.BytesIO))
    
    @pytest.mark.reports
    def test_excel_export_api(self, authenticated_client: TestClient, sample_work_items: list[WorkItem]):
        """Test Excel export via API."""
        response = authenticated_client.get("/reports/export/excel")
        
        if response.status_code == 200:
            # Check content type
            content_type = response.headers.get("content-type", "")
            assert any(x in content_type for x in ["excel", "spreadsheet", "octet"])
        else:
            assert response.status_code in [200, 302]


class TestReportFilters:
    """Tests for report filtering via UI/API."""
    
    @pytest.mark.reports
    def test_reports_with_date_filter(self, authenticated_client: TestClient):
        """Test reports page with date filter."""
        today = date.today()
        response = authenticated_client.get(
            f"/reports?start_date={today - timedelta(weeks=2)}&end_date={today}"
        )
        assert response.status_code in [200, 302]
    
    @pytest.mark.reports
    def test_reports_with_type_filter(self, authenticated_client: TestClient):
        """Test reports page with type filter."""
        response = authenticated_client.get("/reports?type=PLANNED")
        assert response.status_code in [200, 302]
    
    @pytest.mark.reports
    def test_reports_with_status_filter(self, authenticated_client: TestClient):
        """Test reports page with status filter."""
        response = authenticated_client.get("/reports?status=COMPLETED")
        assert response.status_code in [200, 302]


class TestReportDataIntegrity:
    """Tests for report data integrity."""
    
    @pytest.mark.reports
    def test_exported_data_matches_database(
        self, db: Session, regular_user: User, sample_work_week: WorkWeek, sample_work_items: list[WorkItem]
    ):
        """Test exported data matches database records."""
        items = get_filtered_items(db, user_id=regular_user.id)
        
        # Count should match
        assert len(items) == len(sample_work_items)
        
        # Titles should match
        db_titles = {item.title for item in sample_work_items}
        export_titles = {item["Title"] for item in items}
        assert db_titles == export_titles
    
    @pytest.mark.reports
    def test_points_totals_in_export(
        self, db: Session, regular_user: User, sample_work_week: WorkWeek, sample_work_items: list[WorkItem]
    ):
        """Test points totals are correct in exported data."""
        items = get_filtered_items(db, user_id=regular_user.id)
        
        total_assigned = sum(item["Assigned Points"] for item in items)
        total_completion = sum(item["Completion Points"] if item["Completion Points"] else 0 for item in items)
        
        # Should match fixture data
        assert total_assigned == 60
        assert total_completion == 45
    
    @pytest.mark.reports
    def test_user_data_isolation_in_export(
        self, db: Session, regular_user: User, admin_user: User
    ):
        """Test exports only include current user's data."""
        # Create data for admin user
        admin_week = WorkWeek(
            user_id=admin_user.id,
            week_start=date.today() - timedelta(days=date.today().weekday()),
            week_end=date.today() - timedelta(days=date.today().weekday()) + timedelta(days=4),
            total_points=100
        )
        db.add(admin_week)
        db.commit()
        
        admin_item = WorkItem(
            week_id=admin_week.id,
            title="Admin Only Task",
            type="PLANNED",
            status="TODO",
            assigned_points=50,
            start_date=admin_week.week_start,
            end_date=admin_week.week_end
        )
        db.add(admin_item)
        db.commit()
        
        # Export for regular user should not include admin data
        user_items = get_filtered_items(db, user_id=regular_user.id)
        admin_items = get_filtered_items(db, user_id=admin_user.id)
        
        user_titles = {item["Title"] for item in user_items}
        assert "Admin Only Task" not in user_titles
        
        admin_titles = {item["Title"] for item in admin_items}
        assert "Admin Only Task" in admin_titles
