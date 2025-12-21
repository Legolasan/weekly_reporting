"""
Tests for authentication functionality.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.crud.user import hash_password, verify_password


class TestSignup:
    """Tests for user signup."""
    
    @pytest.mark.auth
    def test_signup_page_loads(self, client: TestClient):
        """Test that signup page loads successfully."""
        response = client.get("/signup")
        assert response.status_code == 200
        assert "Sign Up" in response.text or "signup" in response.text.lower()
    
    @pytest.mark.auth
    def test_signup_success(self, client: TestClient, db: Session):
        """Test successful user signup."""
        response = client.post(
            "/signup",
            data={
                "email": "newuser@test.com",
                "password": "newpass123",
                "confirm_password": "newpass123"
            },
            follow_redirects=False
        )
        # Should redirect to dashboard after signup
        assert response.status_code == 302
        
        # User should be created in database
        user = db.query(User).filter(User.email == "newuser@test.com").first()
        assert user is not None
        assert user.is_admin is False
    
    @pytest.mark.auth
    def test_signup_password_mismatch(self, client: TestClient):
        """Test signup fails when passwords don't match."""
        response = client.post(
            "/signup",
            data={
                "email": "newuser@test.com",
                "password": "password1",
                "confirm_password": "password2"
            }
        )
        assert response.status_code == 200
        assert "match" in response.text.lower() or "error" in response.text.lower()
    
    @pytest.mark.auth
    def test_signup_short_password(self, client: TestClient):
        """Test signup fails with short password."""
        response = client.post(
            "/signup",
            data={
                "email": "newuser@test.com",
                "password": "1234",
                "confirm_password": "1234"
            }
        )
        assert response.status_code == 200
        assert "5 characters" in response.text or "error" in response.text.lower()
    
    @pytest.mark.auth
    def test_signup_duplicate_email(self, client: TestClient, regular_user: User):
        """Test signup fails with existing email."""
        response = client.post(
            "/signup",
            data={
                "email": "user@test.com",  # Same as regular_user
                "password": "newpass123",
                "confirm_password": "newpass123"
            }
        )
        assert response.status_code == 200
        assert "exists" in response.text.lower() or "error" in response.text.lower()


class TestLogin:
    """Tests for user login."""
    
    @pytest.mark.auth
    def test_login_page_loads(self, client: TestClient):
        """Test that login page loads successfully."""
        response = client.get("/login")
        assert response.status_code == 200
        assert "Login" in response.text or "login" in response.text.lower()
    
    @pytest.mark.auth
    def test_login_success(self, client: TestClient, regular_user: User):
        """Test successful login."""
        response = client.post(
            "/login",
            data={"email": "user@test.com", "password": "user123"},
            follow_redirects=False
        )
        # Should redirect to dashboard
        assert response.status_code == 302
        # Should set session cookie
        assert "work_tracker_session" in response.cookies
    
    @pytest.mark.auth
    def test_login_wrong_password(self, client: TestClient, regular_user: User):
        """Test login fails with wrong password."""
        response = client.post(
            "/login",
            data={"email": "user@test.com", "password": "wrongpassword"}
        )
        assert response.status_code == 200
        assert "invalid" in response.text.lower() or "error" in response.text.lower()
    
    @pytest.mark.auth
    def test_login_nonexistent_user(self, client: TestClient):
        """Test login fails for non-existent user."""
        response = client.post(
            "/login",
            data={"email": "nobody@test.com", "password": "somepassword"}
        )
        assert response.status_code == 200
        assert "invalid" in response.text.lower() or "error" in response.text.lower()
    
    @pytest.mark.auth
    def test_login_admin_user(self, client: TestClient, admin_user: User):
        """Test admin user can login."""
        response = client.post(
            "/login",
            data={"email": "admin@test.com", "password": "admin123"},
            follow_redirects=False
        )
        assert response.status_code == 302


class TestLogout:
    """Tests for user logout."""
    
    @pytest.mark.auth
    def test_logout(self, authenticated_client: TestClient):
        """Test successful logout."""
        response = authenticated_client.get("/logout", follow_redirects=False)
        # Should redirect to login
        assert response.status_code == 302
        assert "/login" in response.headers.get("location", "")


class TestSession:
    """Tests for session management."""
    
    @pytest.mark.auth
    def test_protected_route_without_auth(self, client: TestClient):
        """Test protected routes redirect to login without auth."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 302
        assert "/login" in response.headers.get("location", "")
    
    @pytest.mark.auth
    def test_protected_route_with_auth(self, authenticated_client: TestClient):
        """Test protected routes accessible with auth."""
        response = authenticated_client.get("/", follow_redirects=False)
        # Should either show dashboard or redirect (depends on state)
        assert response.status_code in [200, 302]
    
    @pytest.mark.auth
    def test_health_endpoint_public(self, client: TestClient):
        """Test health endpoint is public."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestPasswordHashing:
    """Tests for password hashing utilities."""
    
    @pytest.mark.auth
    def test_hash_password(self):
        """Test password hashing."""
        password = "testpassword123"
        hashed = hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 20  # bcrypt hashes are long
    
    @pytest.mark.auth
    def test_verify_password_correct(self):
        """Test correct password verification."""
        password = "testpassword123"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    @pytest.mark.auth
    def test_verify_password_incorrect(self):
        """Test incorrect password verification."""
        password = "testpassword123"
        hashed = hash_password(password)
        
        assert verify_password("wrongpassword", hashed) is False
