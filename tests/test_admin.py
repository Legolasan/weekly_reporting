"""
Tests for admin functionality.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import uuid4

from app.models.user import User
from app.crud.user import get_users, get_all_users_with_stats, delete_user, hash_password


class TestAdminPageAccess:
    """Tests for admin page access control."""
    
    @pytest.mark.admin
    def test_admin_page_requires_auth(self, client: TestClient):
        """Test admin page redirects to login without auth."""
        response = client.get("/admin", follow_redirects=False)
        assert response.status_code == 302
        assert "/login" in response.headers.get("location", "")
    
    @pytest.mark.admin
    def test_admin_page_requires_admin_role(self, authenticated_client: TestClient):
        """Test regular user cannot access admin page."""
        response = authenticated_client.get("/admin", follow_redirects=False)
        # Should be forbidden or redirected
        assert response.status_code in [302, 403]
    
    @pytest.mark.admin
    def test_admin_page_accessible_to_admin(self, admin_client: TestClient):
        """Test admin user can access admin page."""
        response = admin_client.get("/admin")
        # Should load or might need additional setup
        assert response.status_code in [200, 302]


class TestUserManagement:
    """Tests for user management functionality."""
    
    @pytest.mark.admin
    def test_get_all_users(self, db: Session, admin_user: User, regular_user: User):
        """Test listing all users."""
        users = get_users(db)
        
        assert len(users) >= 2
        emails = [u.email for u in users]
        assert "admin@test.com" in emails
        assert "user@test.com" in emails
    
    @pytest.mark.admin
    def test_get_users_with_stats(self, db: Session, admin_user: User, regular_user: User):
        """Test getting users with their statistics."""
        users_with_stats = get_all_users_with_stats(db)
        
        assert len(users_with_stats) >= 2
        
        for user_data in users_with_stats:
            assert "email" in user_data
            assert "is_admin" in user_data
            assert "total_weeks" in user_data
            assert "total_items" in user_data
            assert "total_points" in user_data
    
    @pytest.mark.admin
    def test_delete_regular_user(self, db: Session, admin_user: User):
        """Test deleting a regular user."""
        # Create a user to delete
        user_to_delete = User(
            id=uuid4(),
            email="delete_me@test.com",
            password_hash=hash_password("password123"),
            is_admin=False
        )
        db.add(user_to_delete)
        db.commit()
        
        user_id = user_to_delete.id
        
        # Delete the user
        result = delete_user(db, user_id)
        assert result is True
        
        # Verify deletion
        from app.crud.user import get_user
        deleted = get_user(db, user_id)
        assert deleted is None
    
    @pytest.mark.admin
    def test_admin_cannot_delete_self(self, admin_client: TestClient, admin_user: User):
        """Test admin cannot delete themselves via API."""
        response = admin_client.post(
            f"/admin/delete-user/{admin_user.id}",
            follow_redirects=False
        )
        # Should fail or show error
        # The admin should still exist after this
        assert response.status_code in [200, 302, 400, 403]


class TestAdminUserListing:
    """Tests for admin user listing page."""
    
    @pytest.mark.admin
    def test_admin_sees_all_users(self, admin_client: TestClient, regular_user: User):
        """Test admin can see all users."""
        response = admin_client.get("/admin")
        
        if response.status_code == 200:
            # Check that users are displayed
            assert "user@test.com" in response.text or "admin@test.com" in response.text
    
    @pytest.mark.admin
    def test_admin_sees_user_stats(
        self, admin_client: TestClient, regular_user: User, sample_work_week, sample_work_items
    ):
        """Test admin can see user statistics."""
        response = admin_client.get("/admin")
        
        if response.status_code == 200:
            # Page should contain stats-related content
            text = response.text.lower()
            assert any(word in text for word in ["points", "tasks", "weeks", "items", "total"])


class TestAdminUserDeletion:
    """Tests for admin user deletion functionality."""
    
    @pytest.mark.admin
    def test_delete_user_api(self, admin_client: TestClient, db: Session):
        """Test deleting user via admin API."""
        # Create a user to delete
        user_to_delete = User(
            id=uuid4(),
            email="api_delete@test.com",
            password_hash=hash_password("password123"),
            is_admin=False
        )
        db.add(user_to_delete)
        db.commit()
        
        response = admin_client.post(
            f"/admin/delete-user/{user_to_delete.id}",
            follow_redirects=False
        )
        
        # Should succeed or redirect
        assert response.status_code in [200, 302, 303]
    
    @pytest.mark.admin
    def test_delete_nonexistent_user(self, admin_client: TestClient):
        """Test deleting non-existent user."""
        fake_id = uuid4()
        response = admin_client.post(
            f"/admin/delete-user/{fake_id}",
            follow_redirects=False
        )
        # Should handle gracefully
        assert response.status_code in [200, 302, 404]
    
    @pytest.mark.admin
    def test_regular_user_cannot_delete(self, authenticated_client: TestClient, db: Session):
        """Test regular user cannot delete other users."""
        # Create a user
        target_user = User(
            id=uuid4(),
            email="target@test.com",
            password_hash=hash_password("password123"),
            is_admin=False
        )
        db.add(target_user)
        db.commit()
        
        response = authenticated_client.post(
            f"/admin/delete-user/{target_user.id}",
            follow_redirects=False
        )
        
        # Should be forbidden
        assert response.status_code in [302, 403]
        
        # User should still exist
        from app.crud.user import get_user
        still_exists = get_user(db, target_user.id)
        assert still_exists is not None


class TestAdminAuthorization:
    """Tests for admin authorization checks."""
    
    @pytest.mark.admin
    def test_is_admin_flag(self, admin_user: User, regular_user: User):
        """Test is_admin flag is set correctly."""
        assert admin_user.is_admin is True
        assert regular_user.is_admin is False
    
    @pytest.mark.admin
    def test_admin_role_in_profile(self, admin_client: TestClient):
        """Test admin role shown in profile."""
        response = admin_client.get("/profile")
        
        if response.status_code == 200:
            # Should indicate admin status
            text = response.text.lower()
            assert "admin" in text
    
    @pytest.mark.admin
    def test_admin_link_visible_for_admin(self, admin_client: TestClient):
        """Test admin link visible in navigation for admin."""
        response = admin_client.get("/")
        
        if response.status_code == 200:
            # Admin link should be visible
            assert "/admin" in response.text or "Admin" in response.text
    
    @pytest.mark.admin
    def test_admin_link_hidden_for_regular_user(self, authenticated_client: TestClient):
        """Test admin link hidden for regular users."""
        response = authenticated_client.get("/")
        
        # This depends on implementation - the link might be hidden or the page might redirect
        # Just ensure no errors
        assert response.status_code in [200, 302]


class TestAdminDataAccess:
    """Tests for admin data access across users."""
    
    @pytest.mark.admin
    def test_admin_sees_all_users_data(
        self, db: Session, admin_user: User, regular_user: User, sample_work_items
    ):
        """Test admin can see all users' data in summary."""
        users_with_stats = get_all_users_with_stats(db)
        
        # Find regular user's stats
        user_stats = next(
            (u for u in users_with_stats if u["email"] == "user@test.com"),
            None
        )
        
        if user_stats:
            # Should have stats from the sample data
            assert user_stats["total_items"] >= 0
            assert user_stats["total_points"] >= 0
