"""API routes for the Staff Management service."""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from datetime import datetime

from src.common.metrics import record_request
from src.common.logging import get_logger
from src.common.fastapi_auth import (
    verify_staff_access,
    get_current_user,
    require_admin_access,
    security,
)
from fastapi.security import HTTPAuthorizationCredentials

from .models import (
    User,
    UserCreate,
    UserUpdate,
    UserListResponse,
    Ticket,
    TicketCreate,
    TicketUpdate,
    TicketListResponse,
    SystemStats,
    SystemHealth,
    DashboardStats,
    StaffResponse,
)

router = APIRouter(prefix="/staff", tags=["staff-management"])
logger = get_logger("staff_routes")

# Dependency wrappers to allow test patching to work reliably
def get_current_user_dependency(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    return get_current_user(credentials)


def verify_staff_access_dependency(current_user: dict = Depends(get_current_user_dependency)) -> None:
    return verify_staff_access(current_user)


def require_admin_access_dependency(current_user: dict = Depends(get_current_user_dependency)) -> None:
    return require_admin_access(current_user)


# Dashboard endpoint
@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard(
    current_user: dict = Depends(get_current_user_dependency),
    _: None = Depends(verify_staff_access_dependency),
) -> DashboardStats:
    """Get staff dashboard data including stats and recent activity."""
    record_request("staff-dashboard")
    logger.info(f"Dashboard accessed by {current_user.get('email', 'unknown')}")

    try:
        # Mock data for now - will be replaced with real database queries
        system_stats = SystemStats(
            total_users=12847,
            active_users=8234,
            total_subscriptions=8234,
            active_subscriptions=8234,
            open_tickets=23,
            closed_tickets=156,
            system_uptime="99.9%",
            avg_response_time=2.4,
        )

        recent_tickets = [
            Ticket(
                id="T-2024-001",
                title="API Rate Limiting Issues",
                description="Experiencing unexpected rate limiting on API calls despite being under the limit.",
                customer={
                    "name": "John Doe",
                    "email": "john.doe@example.com",
                    "plan": "Pro",
                },
                status="in-progress",
                priority="high",
                category="API",
                assigned_to="Sarah Wilson",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                response_time=2.5,
                message_count=4,
            )
        ]

        system_alerts = [
            {
                "id": 1,
                "type": "warning",
                "message": "API Gateway response time increased by 15%",
                "time": "5 minutes ago",
            }
        ]

        quick_actions = [
            {
                "name": "Create User",
                "description": "Add a new user account",
                "href": "/staff/users/create",
                "icon": "UserGroupIcon",
                "color": "from-blue-500 to-blue-600",
            }
        ]

        return DashboardStats(
            system_stats=system_stats,
            recent_tickets=recent_tickets,
            system_alerts=system_alerts,
            quick_actions=quick_actions,
        )

    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to load dashboard: {str(e)}"
        )


# System statistics endpoint
@router.get("/stats", response_model=SystemStats)
async def get_system_stats(
    current_user: dict = Depends(get_current_user_dependency),
    _: None = Depends(verify_staff_access_dependency),
) -> SystemStats:
    """Get system statistics."""
    record_request("staff-stats")
    logger.info("System stats requested")

    try:
        # Mock data - replace with real database queries
        return SystemStats(
            total_users=12847,
            active_users=8234,
            total_subscriptions=8234,
            active_subscriptions=8234,
            open_tickets=23,
            closed_tickets=156,
            system_uptime="99.9%",
            avg_response_time=2.4,
        )
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


# System health endpoint
@router.get("/health/system", response_model=SystemHealth)
async def get_system_health(
    current_user: dict = Depends(get_current_user_dependency),
    _: None = Depends(verify_staff_access_dependency),
) -> SystemHealth:
    """Get detailed system health information."""
    record_request("staff-system-health")
    logger.info("System health check requested")

    try:
        return SystemHealth(
            api_performance={
                "status": "healthy",
                "success_rate": 94.0,
                "avg_response_time": 235,
            },
            database_status={
                "status": "optimal",
                "utilization": 89.0,
                "connection_pool": "healthy",
            },
            memory_usage={
                "status": "moderate",
                "usage_percent": 67.0,
                "available_gb": 12.4,
            },
            service_status={
                "model_router": "healthy",
                "plan_management": "healthy",
                "git_worktree": "healthy",
                "workflow_orchestrator": "healthy",
                "verification_feedback": "healthy",
            },
        )
    except Exception as e:
        logger.error(f"System health error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get system health: {str(e)}"
        )


# USER MANAGEMENT ENDPOINTS


@router.get("/users", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    role: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user_dependency),
    _: None = Depends(verify_staff_access_dependency),
) -> UserListResponse:
    """List users with filtering and pagination."""
    record_request("staff-users-list")
    logger.info(f"User list requested by {current_user.get('email', 'unknown')}")

    # Mock data with multiple users for better testing
    mock_users = [
        User(
            id="1",
            name="John Doe",
            email="john.doe@example.com",
            role="customer",
            status="active",
            plan="Pro",
            created_at=datetime(2023, 6, 15),
            updated_at=datetime.now(),
            total_spent=237.0,
            api_calls=15847,
        ),
        User(
            id="2",
            name="Jane Smith",
            email="jane.smith@company.com",
            role="customer",
            status="active",
            plan="Enterprise",
            created_at=datetime(2023, 3, 22),
            updated_at=datetime.now(),
            total_spent=1200.0,
            api_calls=45231,
        ),
        User(
            id="3",
            name="Mike Johnson",
            email="mike@startup.io",
            role="customer",
            status="inactive",
            plan="Standard",
            created_at=datetime(2023, 11, 8),
            updated_at=datetime.now(),
            total_spent=87.0,
            api_calls=3421,
        ),
        User(
            id="4",
            name="Sarah Wilson",
            email="sarah.wilson@staff.com",
            role="support",
            status="active",
            plan="Staff",
            created_at=datetime(2023, 1, 15),
            updated_at=datetime.now(),
            total_spent=0.0,
            api_calls=0,
        ),
        User(
            id="5",
            name="Alex Chen",
            email="alex.chen@admin.com",
            role="manager",
            status="active",
            plan="Staff",
            created_at=datetime(2022, 8, 10),
            updated_at=datetime.now(),
            total_spent=0.0,
            api_calls=0,
        ),
    ]

    # Apply filtering
    filtered_users = mock_users
    if role:
        filtered_users = [u for u in filtered_users if u.role == role]
    if status:
        filtered_users = [u for u in filtered_users if u.status == status]
    if search:
        search_lower = search.lower()
        filtered_users = [
            u
            for u in filtered_users
            if search_lower in u.name.lower() or search_lower in u.email.lower()
        ]

    # Apply pagination
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_users = filtered_users[start_idx:end_idx]

    return UserListResponse(
        users=paginated_users, total=len(filtered_users), page=page, per_page=per_page
    )


@router.get("/users/{user_id}", response_model=User)
async def get_user(
    user_id: str,
    current_user: dict = Depends(get_current_user_dependency),
    _: None = Depends(verify_staff_access_dependency),
) -> User:
    """Get a specific user by ID."""
    record_request("staff-users-get")
    logger.info(f"User {user_id} requested by {current_user.get('email', 'unknown')}")

    # Mock user lookup
    if user_id == "1":
        return User(
            id="1",
            name="John Doe",
            email="john.doe@example.com",
            role="customer",
            status="active",
            plan="Pro",
            created_at=datetime(2023, 6, 15),
            updated_at=datetime.now(),
            total_spent=237.0,
            api_calls=15847,
            last_active=datetime.now(),
        )

    raise HTTPException(status_code=404, detail="User not found")


@router.post("/users", response_model=StaffResponse)
async def create_user(
    user_data: UserCreate,
    current_user: dict = Depends(get_current_user_dependency),
    _: None = Depends(require_admin_access_dependency),  # Only admins can create users
) -> StaffResponse:
    """Create a new user."""
    record_request("staff-users-create")
    logger.info(f"User creation requested by {current_user.get('email', 'unknown')}")

    try:
        # In real implementation, this would:
        # 1. Validate user data
        # 2. Check for existing email
        # 3. Hash password
        # 4. Save to database
        # 5. Send welcome email

        logger.info(f"Creating user: {user_data.email}")

        # Mock successful creation
        new_user_id = f"user_{datetime.now().timestamp()}"

        return StaffResponse(
            success=True,
            message=f"User {user_data.email} created successfully",
            data={"user_id": new_user_id},
        )

    except Exception as e:
        logger.error(f"User creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")


@router.put("/users/{user_id}", response_model=StaffResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: dict = Depends(get_current_user_dependency),
    _: None = Depends(verify_staff_access_dependency),
) -> StaffResponse:
    """Update an existing user."""
    record_request("staff-users-update")
    logger.info(
        f"User {user_id} update requested by {current_user.get('email', 'unknown')}"
    )

    try:
        # Check if user exists (mock)
        if user_id not in ["1", "2", "3", "4", "5"]:
            raise HTTPException(status_code=404, detail="User not found")

        # In real implementation, this would:
        # 1. Validate update data
        # 2. Check permissions (staff can only update certain fields)
        # 3. Update user in database
        # 4. Log the changes

        updated_fields = []
        if user_data.name:
            updated_fields.append("name")
        if user_data.email:
            updated_fields.append("email")
        if user_data.role:
            updated_fields.append("role")
        if user_data.status:
            updated_fields.append("status")

        logger.info(f"Updating user {user_id} fields: {updated_fields}")

        return StaffResponse(
            success=True,
            message=f"User {user_id} updated successfully",
            data={"updated_fields": updated_fields},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User update failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update user: {str(e)}")


@router.delete("/users/{user_id}", response_model=StaffResponse)
async def delete_user(
    user_id: str,
    current_user: dict = Depends(get_current_user_dependency),
    _: None = Depends(require_admin_access_dependency),  # Only admins can delete users
) -> StaffResponse:
    """Delete a user (soft delete)."""
    record_request("staff-users-delete")
    logger.info(
        f"User {user_id} deletion requested by {current_user.get('email', 'unknown')}"
    )

    try:
        # Check if user exists (mock)
        if user_id not in ["1", "2", "3", "4", "5"]:
            raise HTTPException(status_code=404, detail="User not found")

        # Prevent self-deletion
        if current_user.get("user_id") == user_id:
            raise HTTPException(
                status_code=400, detail="Cannot delete your own account"
            )

        # In real implementation, this would:
        # 1. Perform soft delete (set status to inactive)
        # 2. Anonymize or archive user data
        # 3. Revoke all tokens/sessions
        # 4. Log the deletion

        logger.info(f"Soft deleting user {user_id}")

        return StaffResponse(
            success=True,
            message=f"User {user_id} deleted successfully",
            data={"deletion_type": "soft_delete"},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User deletion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete user: {str(e)}")


@router.patch("/users/{user_id}/suspend", response_model=StaffResponse)
async def suspend_user(
    user_id: str,
    current_user: dict = Depends(get_current_user_dependency),
    _: None = Depends(verify_staff_access_dependency),
) -> StaffResponse:
    """Suspend a user account."""
    record_request("staff-users-suspend")
    logger.info(
        f"User {user_id} suspension requested by {current_user.get('email', 'unknown')}"
    )

    try:
        # Check if user exists (mock)
        if user_id not in ["1", "2", "3", "4", "5"]:
            raise HTTPException(status_code=404, detail="User not found")

        # Prevent self-suspension
        if current_user.get("user_id") == user_id:
            raise HTTPException(
                status_code=400, detail="Cannot suspend your own account"
            )

        # In real implementation, this would:
        # 1. Set user status to suspended
        # 2. Revoke active sessions
        # 3. Block API access
        # 4. Send notification

        logger.info(f"Suspending user {user_id}")

        return StaffResponse(
            success=True,
            message=f"User {user_id} suspended successfully",
            data={"new_status": "suspended"},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User suspension failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to suspend user: {str(e)}")


@router.patch("/users/{user_id}/activate", response_model=StaffResponse)
async def activate_user(
    user_id: str,
    current_user: dict = Depends(get_current_user_dependency),
    _: None = Depends(verify_staff_access_dependency),
) -> StaffResponse:
    """Activate a suspended user account."""
    record_request("staff-users-activate")
    logger.info(
        f"User {user_id} activation requested by {current_user.get('email', 'unknown')}"
    )

    try:
        # Check if user exists (mock)
        if user_id not in ["1", "2", "3", "4", "5"]:
            raise HTTPException(status_code=404, detail="User not found")

        # In real implementation, this would:
        # 1. Set user status to active
        # 2. Restore API access
        # 3. Send notification

        logger.info(f"Activating user {user_id}")

        return StaffResponse(
            success=True,
            message=f"User {user_id} activated successfully",
            data={"new_status": "active"},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User activation failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to activate user: {str(e)}"
        )


# SUPPORT TICKET MANAGEMENT ENDPOINTS


@router.get("/tickets", response_model=TicketListResponse)
async def list_tickets(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user_dependency),
    _: None = Depends(verify_staff_access_dependency),
) -> TicketListResponse:
    """List tickets with optional filtering."""
    record_request("staff-tickets-list")
    logger.info(f"Tickets list requested by {current_user.get('email', 'unknown')}")

    try:
        # Mock data - in real implementation, this would query the database
        mock_tickets = [
            Ticket(
                id="T-2024-001",
                title="API Rate Limiting Issues",
                description="Experiencing unexpected rate limiting on API calls despite being under the limit.",
                customer={
                    "name": "John Doe",
                    "email": "john.doe@example.com",
                    "plan": "Pro",
                },
                status="in-progress",
                priority="high",
                category="API",
                assigned_to="Sarah Wilson",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                response_time=2.5,
                message_count=4,
            ),
            Ticket(
                id="T-2024-002",
                title="Billing System Integration",
                description="Need to integrate with new billing system for automated invoicing.",
                customer={
                    "name": "Jane Smith",
                    "email": "jane.smith@example.com",
                    "plan": "Enterprise",
                },
                status="open",
                priority="medium",
                category="Billing",
                assigned_to="Mike Johnson",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                response_time=1.2,
                message_count=2,
            ),
        ]

        # Apply filters
        filtered_tickets = mock_tickets
        if status:
            filtered_tickets = [t for t in filtered_tickets if t.status == status]
        if priority:
            filtered_tickets = [t for t in filtered_tickets if t.priority == priority]
        if category:
            filtered_tickets = [t for t in filtered_tickets if t.category == category]
        if search:
            search_lower = search.lower()
            filtered_tickets = [
                t for t in filtered_tickets
                if search_lower in t.title.lower() or search_lower in t.description.lower()
            ]

        # Pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_tickets = filtered_tickets[start_idx:end_idx]

        return TicketListResponse(
            tickets=paginated_tickets,
            total=len(filtered_tickets),
            page=page,
            per_page=per_page,
            total_pages=(len(filtered_tickets) + per_page - 1) // per_page,
        )

    except Exception as e:
        logger.error(f"Ticket list error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to list tickets: {str(e)}"
        )


@router.get("/tickets/stats", response_model=Dict[str, Any])
async def get_ticket_stats(
    current_user: dict = Depends(get_current_user),
    _: None = Depends(verify_staff_access),
) -> Dict[str, Any]:
    """Get ticket statistics and metrics."""
    record_request("staff-tickets-stats")
    logger.info(f"Ticket stats requested by {current_user.get('email', 'unknown')}")

    try:
        # Mock statistics
        return {
            "total_tickets": 5,
            "by_status": {
                "open": 2,
                "in-progress": 1,
                "waiting-customer": 1,
                "resolved": 1,
                "closed": 0,
            },
            "by_priority": {"low": 1, "medium": 2, "high": 1, "urgent": 1},
            "by_category": {
                "API": 1,
                "Billing": 1,
                "Performance": 1,
                "Feature Request": 1,
                "Security": 1,
            },
            "avg_response_time": 2.8,  # hours
            "avg_resolution_time": 24.5,  # hours
            "satisfaction_score": 4.2,  # out of 5
        }

    except Exception as e:
        logger.error(f"Ticket stats error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get ticket stats: {str(e)}"
        )


# Place stats endpoint before parameterized ticket route to avoid any ambiguity
@router.get("/tickets/stats", response_model=Dict[str, Any])
async def get_ticket_stats(
    current_user: dict = Depends(get_current_user_dependency),
    _: None = Depends(verify_staff_access_dependency),
) -> Dict[str, Any]:
    """Get ticket statistics and metrics."""
    record_request("staff-tickets-stats")
    logger.info(f"Ticket stats requested by {current_user.get('email', 'unknown')}")

    try:
        # Mock statistics
        return {
            "total_tickets": 5,
            "by_status": {
                "open": 2,
                "in-progress": 1,
                "waiting-customer": 1,
                "resolved": 1,
                "closed": 0,
            },
            "by_priority": {"low": 1, "medium": 2, "high": 1, "urgent": 1},
            "by_category": {
                "API": 1,
                "Billing": 1,
                "Performance": 1,
                "Feature Request": 1,
                "Security": 1,
            },
            "avg_response_time": 2.8,  # hours
            "avg_resolution_time": 24.5,  # hours
            "satisfaction_score": 4.2,  # out of 5
        }

    except Exception as e:
        logger.error(f"Ticket stats error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get ticket stats: {str(e)}"
        )


@router.get("/tickets/{ticket_id}", response_model=Ticket)
async def get_ticket(
    ticket_id: str,
    current_user: dict = Depends(get_current_user_dependency),
    _: None = Depends(verify_staff_access_dependency),
) -> Ticket:
    """Get a specific ticket by ID."""
    record_request("staff-tickets-get")
    logger.info(
        f"Ticket {ticket_id} requested by {current_user.get('email', 'unknown')}"
    )

    # Mock ticket lookup
    if ticket_id == "T-2024-001":
        return Ticket(
            id="T-2024-001",
            title="API Rate Limiting Issues",
            description="Experiencing unexpected rate limiting on API calls despite being under the limit. This started happening after the last API update.",
            status="in-progress",
            priority="high",
            category="API",
            customer={
                "name": "John Doe",
                "email": "john.doe@example.com",
                "plan": "Pro",
            },
            assigned_to="Sarah Wilson",
            created_at=datetime(2024, 1, 20, 10, 30),
            updated_at=datetime(2024, 1, 21, 14, 15),
            response_time=2.5,
            message_count=4,
        )

    raise HTTPException(status_code=404, detail="Ticket not found")


@router.post("/tickets", response_model=StaffResponse)
async def create_ticket(
    ticket_data: TicketCreate,
    current_user: dict = Depends(get_current_user_dependency),
    _: None = Depends(verify_staff_access_dependency),
) -> StaffResponse:
    """Create a new support ticket."""
    record_request("staff-tickets-create")
    logger.info(f"Ticket creation requested by {current_user.get('email', 'unknown')}")

    try:
        # In real implementation, this would:
        # 1. Validate ticket data
        # 2. Check customer exists
        # 3. Generate unique ticket ID
        # 4. Save to database
        # 5. Send notifications

        # Generate new ticket ID
        import time

        new_ticket_id = (
            f"T-{datetime.now().strftime('%Y')}-{int(time.time() % 10000):04d}"
        )

        logger.info(f"Creating ticket: {new_ticket_id}")

        return StaffResponse(
            success=True,
            message=f"Ticket {new_ticket_id} created successfully",
            data={
                "ticket_id": new_ticket_id,
                "customer_id": ticket_data.customer_id,
                "priority": ticket_data.priority,
                "category": ticket_data.category,
            },
        )

    except Exception as e:
        logger.error(f"Ticket creation failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create ticket: {str(e)}"
        )


@router.put("/tickets/{ticket_id}", response_model=StaffResponse)
async def update_ticket(
    ticket_id: str,
    ticket_data: TicketUpdate,
    current_user: dict = Depends(get_current_user_dependency),
    _: None = Depends(verify_staff_access_dependency),
) -> StaffResponse:
    """Update an existing ticket."""
    record_request("staff-tickets-update")
    logger.info(
        f"Ticket {ticket_id} update requested by {current_user.get('email', 'unknown')}"
    )

    try:
        # Check if ticket exists (mock)
        valid_tickets = [
            "T-2024-001",
            "T-2024-002",
            "T-2024-003",
            "T-2024-004",
            "T-2024-005",
        ]
        if ticket_id not in valid_tickets:
            raise HTTPException(status_code=404, detail="Ticket not found")

        # In real implementation, this would:
        # 1. Validate update data
        # 2. Check permissions (who can update what)
        # 3. Update ticket in database
        # 4. Log the changes
        # 5. Send notifications if needed

        updated_fields = []
        if ticket_data.title:
            updated_fields.append("title")
        if ticket_data.description:
            updated_fields.append("description")
        if ticket_data.status:
            updated_fields.append("status")
        if ticket_data.priority:
            updated_fields.append("priority")
        if ticket_data.category:
            updated_fields.append("category")
        if ticket_data.assigned_to:
            updated_fields.append("assigned_to")

        logger.info(f"Updating ticket {ticket_id} fields: {updated_fields}")

        return StaffResponse(
            success=True,
            message=f"Ticket {ticket_id} updated successfully",
            data={
                "updated_fields": updated_fields,
                "updated_by": current_user.get("email", "unknown"),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ticket update failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update ticket: {str(e)}"
        )


@router.patch("/tickets/{ticket_id}/assign", response_model=StaffResponse)
async def assign_ticket(
    ticket_id: str,
    assign_to: str,
    current_user: dict = Depends(get_current_user_dependency),
    _: None = Depends(verify_staff_access_dependency),
) -> StaffResponse:
    """Assign a ticket to a staff member."""
    record_request("staff-tickets-assign")
    logger.info(
        f"Ticket {ticket_id} assignment requested by {current_user.get('email', 'unknown')}"
    )

    try:
        # Check if ticket exists (mock)
        valid_tickets = [
            "T-2024-001",
            "T-2024-002",
            "T-2024-003",
            "T-2024-004",
            "T-2024-005",
        ]
        if ticket_id not in valid_tickets:
            raise HTTPException(status_code=404, detail="Ticket not found")

        # In real implementation, this would:
        # 1. Validate assignee exists and is staff
        # 2. Update ticket assignment
        # 3. Send notification to assignee
        # 4. Log the assignment

        logger.info(f"Assigning ticket {ticket_id} to {assign_to}")

        return StaffResponse(
            success=True,
            message=f"Ticket {ticket_id} assigned to {assign_to}",
            data={
                "assigned_to": assign_to,
                "assigned_by": current_user.get("email", "unknown"),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ticket assignment failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to assign ticket: {str(e)}"
        )


@router.patch("/tickets/{ticket_id}/status", response_model=StaffResponse)
async def update_ticket_status(
    ticket_id: str,
    new_status: str,
    current_user: dict = Depends(get_current_user_dependency),
    _: None = Depends(verify_staff_access_dependency),
) -> StaffResponse:
    """Update ticket status."""
    record_request("staff-tickets-status")
    logger.info(
        f"Ticket {ticket_id} status update requested by {current_user.get('email', 'unknown')}"
    )

    try:
        # Check if ticket exists (mock)
        valid_tickets = [
            "T-2024-001",
            "T-2024-002",
            "T-2024-003",
            "T-2024-004",
            "T-2024-005",
        ]
        if ticket_id not in valid_tickets:
            raise HTTPException(status_code=404, detail="Ticket not found")

        # Validate status
        valid_statuses = [
            "open",
            "in-progress",
            "waiting-customer",
            "resolved",
            "closed",
        ]
        if new_status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {valid_statuses}",
            )

        # In real implementation, this would:
        # 1. Update ticket status
        # 2. Handle status-specific logic (notifications, etc.)
        # 3. Log the status change

        logger.info(f"Updating ticket {ticket_id} status to {new_status}")

        return StaffResponse(
            success=True,
            message=f"Ticket {ticket_id} status updated to {new_status}",
            data={
                "new_status": new_status,
                "updated_by": current_user.get("email", "unknown"),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ticket status update failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update ticket status: {str(e)}"
        )


@router.patch("/tickets/{ticket_id}/priority", response_model=StaffResponse)
async def update_ticket_priority(
    ticket_id: str,
    new_priority: str,
    current_user: dict = Depends(get_current_user_dependency),
    _: None = Depends(verify_staff_access_dependency),
) -> StaffResponse:
    """Update ticket priority."""
    record_request("staff-tickets-priority")
    logger.info(
        f"Ticket {ticket_id} priority update requested by {current_user.get('email', 'unknown')}"
    )

    try:
        # Check if ticket exists (mock)
        valid_tickets = [
            "T-2024-001",
            "T-2024-002",
            "T-2024-003",
            "T-2024-004",
            "T-2024-005",
        ]
        if ticket_id not in valid_tickets:
            raise HTTPException(status_code=404, detail="Ticket not found")

        # Validate priority
        valid_priorities = ["low", "medium", "high", "urgent"]
        if new_priority not in valid_priorities:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid priority. Must be one of: {valid_priorities}",
            )

        # In real implementation, this would:
        # 1. Update ticket priority
        # 2. Handle priority-specific logic (escalations, etc.)
        # 3. Log the priority change

        logger.info(f"Updating ticket {ticket_id} priority to {new_priority}")

        return StaffResponse(
            success=True,
            message=f"Ticket {ticket_id} priority updated to {new_priority}",
            data={
                "new_priority": new_priority,
                "updated_by": current_user.get("email", "unknown"),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ticket priority update failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update ticket priority: {str(e)}"
        )


## moved earlier
