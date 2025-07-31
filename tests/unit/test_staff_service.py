"""Unit tests for Staff Management service."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from src.staff.models import UserCreate, TicketCreate

from src.staff.app import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_auth():
    """Mock authentication for testing."""
    mock_user = {
        "user_id": "test-admin",
        "username": "admin",
        "email": "admin@test.com",
        "role": "admin",
        "roles": ["admin"]
    }
    return mock_user


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_check(self, client):
        """Test health check returns 200."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestStaffDashboard:
    """Test staff dashboard endpoints."""
    
    @patch("src.staff.routes.get_current_user")
    @patch("src.staff.routes.verify_staff_access")
    def test_dashboard_access_admin(self, mock_verify, mock_get_user, client, mock_auth):
        """Test dashboard access with admin user."""
        mock_get_user.return_value = mock_auth
        mock_verify.return_value = None
        
        response = client.get(
            "/staff/dashboard",
            headers={"Authorization": "Bearer mock-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "system_stats" in data
        assert "recent_tickets" in data
        assert "system_alerts" in data
        assert "quick_actions" in data
    
    @patch("src.staff.routes.get_current_user")
    @patch("src.staff.routes.verify_staff_access")
    def test_system_stats(self, mock_verify, mock_get_user, client, mock_auth):
        """Test system stats endpoint."""
        mock_get_user.return_value = mock_auth
        mock_verify.return_value = None
        
        response = client.get(
            "/staff/stats", 
            headers={"Authorization": "Bearer mock-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data
        assert "active_users" in data
        assert "open_tickets" in data
        assert "system_uptime" in data


class TestUserManagement:
    """Test user management endpoints."""
    
    @patch("src.staff.routes.get_current_user")
    @patch("src.staff.routes.verify_staff_access")
    def test_list_users(self, mock_verify, mock_get_user, client, mock_auth):
        """Test listing users."""
        mock_get_user.return_value = mock_auth
        mock_verify.return_value = None
        
        response = client.get(
            "/staff/users",
            headers={"Authorization": "Bearer mock-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
    
    @patch("src.staff.routes.get_current_user")
    @patch("src.staff.routes.verify_staff_access")
    def test_list_users_with_filters(self, mock_verify, mock_get_user, client, mock_auth):
        """Test listing users with filters."""
        mock_get_user.return_value = mock_auth
        mock_verify.return_value = None
        
        response = client.get(
            "/staff/users?role=admin&status=active&search=admin",
            headers={"Authorization": "Bearer mock-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
    
    @patch("src.staff.routes.get_current_user")
    @patch("src.staff.routes.verify_staff_access") 
    def test_get_user(self, mock_verify, mock_get_user, client, mock_auth):
        """Test getting specific user."""
        mock_get_user.return_value = mock_auth
        mock_verify.return_value = None
        
        response = client.get(
            "/staff/users/1",
            headers={"Authorization": "Bearer mock-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "1"
        assert "name" in data
        assert "email" in data
    
    @patch("src.staff.routes.get_current_user")
    @patch("src.staff.routes.require_admin_access")
    def test_create_user(self, mock_require_admin, mock_get_user, client, mock_auth):
        """Test creating new user."""
        mock_get_user.return_value = mock_auth
        mock_require_admin.return_value = None
        
        user_data = {
            "name": "Test User",
            "email": "test@example.com", 
            "role": "customer",
            "status": "active",
            "password": "securepassword123"
        }
        
        response = client.post(
            "/staff/users",
            json=user_data,
            headers={"Authorization": "Bearer mock-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "created successfully" in data["message"]
    
    @patch("src.staff.routes.get_current_user") 
    @patch("src.staff.routes.verify_staff_access")
    def test_update_user(self, mock_verify, mock_get_user, client, mock_auth):
        """Test updating user."""
        mock_get_user.return_value = mock_auth
        mock_verify.return_value = None
        
        update_data = {
            "name": "Updated Name",
            "status": "inactive"
        }
        
        response = client.put(
            "/staff/users/1",
            json=update_data,
            headers={"Authorization": "Bearer mock-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "updated successfully" in data["message"]


class TestTicketManagement:
    """Test ticket management endpoints."""
    
    @patch("src.staff.routes.get_current_user")
    @patch("src.staff.routes.verify_staff_access")
    def test_list_tickets(self, mock_verify, mock_get_user, client, mock_auth):
        """Test listing tickets."""
        mock_get_user.return_value = mock_auth
        mock_verify.return_value = None
        
        response = client.get(
            "/staff/tickets",
            headers={"Authorization": "Bearer mock-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "tickets" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
    
    @patch("src.staff.routes.get_current_user")
    @patch("src.staff.routes.verify_staff_access")
    def test_get_ticket(self, mock_verify, mock_get_user, client, mock_auth):
        """Test getting specific ticket."""
        mock_get_user.return_value = mock_auth
        mock_verify.return_value = None
        
        response = client.get(
            "/staff/tickets/T-2024-001",
            headers={"Authorization": "Bearer mock-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "T-2024-001"
        assert "title" in data
        assert "status" in data
        assert "customer" in data
    
    @patch("src.staff.routes.get_current_user")
    @patch("src.staff.routes.verify_staff_access")
    def test_create_ticket(self, mock_verify, mock_get_user, client, mock_auth):
        """Test creating new ticket."""
        mock_get_user.return_value = mock_auth
        mock_verify.return_value = None
        
        ticket_data = {
            "title": "Test Issue",
            "description": "Test description",
            "priority": "medium",
            "category": "Bug Report",
            "customer_id": "customer123"
        }
        
        response = client.post(
            "/staff/tickets",
            json=ticket_data,
            headers={"Authorization": "Bearer mock-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "created successfully" in data["message"]
    
    @patch("src.staff.routes.get_current_user")
    @patch("src.staff.routes.verify_staff_access")
    def test_update_ticket_status(self, mock_verify, mock_get_user, client, mock_auth):
        """Test updating ticket status."""
        mock_get_user.return_value = mock_auth
        mock_verify.return_value = None
        
        response = client.patch(
            "/staff/tickets/T-2024-001/status?new_status=resolved",
            headers={"Authorization": "Bearer mock-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "status updated" in data["message"]
    
    @patch("src.staff.routes.get_current_user")
    @patch("src.staff.routes.verify_staff_access")
    def test_ticket_stats(self, mock_verify, mock_get_user, client, mock_auth):
        """Test ticket statistics."""
        mock_get_user.return_value = mock_auth
        mock_verify.return_value = None
        
        response = client.get(
            "/staff/tickets/stats",
            headers={"Authorization": "Bearer mock-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total_tickets" in data
        assert "by_status" in data
        assert "by_priority" in data
        assert "avg_response_time" in data


class TestAuthentication:
    """Test authentication and authorization."""
    
    def test_dashboard_without_auth(self, client):
        """Test dashboard access without authentication."""
        response = client.get("/staff/dashboard")
        assert response.status_code == 401
    
    def test_users_without_auth(self, client):
        """Test user endpoints without authentication."""
        response = client.get("/staff/users")
        assert response.status_code == 401
    
    def test_tickets_without_auth(self, client):
        """Test ticket endpoints without authentication."""
        response = client.get("/staff/tickets")
        assert response.status_code == 401


@pytest.mark.integration
class TestStaffServiceIntegration:
    """Integration tests for staff service."""
    
    def test_service_configuration(self):
        """Test service configuration loads correctly."""
        from src.staff.config import settings
        
        assert settings.service_name == "staff-service"
        assert settings.service_port == 8006
        assert settings.require_auth is True
    
    def test_models_validation(self):
        """Test model validation."""
        
        # Test valid user creation
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "role": "customer",
            "password": "securepass123"
        }
        user = UserCreate(**user_data)
        assert user.name == "Test User"
        assert user.role == "customer"
        
        # Test valid ticket creation
        ticket_data = {
            "title": "Test Ticket",
            "description": "Test description",
            "priority": "medium",
            "category": "Bug Report",
            "customer_id": "customer123"
        }
        ticket = TicketCreate(**ticket_data)
        assert ticket.title == "Test Ticket"
        assert ticket.priority == "medium"