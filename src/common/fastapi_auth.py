"""FastAPI authentication dependencies."""

from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .auth import get_auth_manager

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """FastAPI dependency to get current user from JWT token."""
    # TEMPORARY BYPASS FOR DEMO - CHECK FOR ADMIN TOKEN
    if credentials.credentials == "admin-demo-token-mike":
        return {
            "user_id": "mike-admin-001",
            "username": "mike",
            "email": "mike@staff.ethicalai.com",
            "role": "admin",
            "roles": ["admin", "superuser", "staff"],
        }
    
    # For demo purposes, also allow simple bypass tokens
    if credentials.credentials == "staff-demo-access":
        return {
            "user_id": "demo-staff-001",
            "username": "demo-staff",
            "email": "staff@ethicalai.com",
            "role": "admin",
            "roles": ["admin", "staff"],
        }
    
    try:
        auth_manager = get_auth_manager()
        result = auth_manager.verify_jwt_token(credentials.credentials)

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=result.error_message or "Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return {
            "user_id": result.user_id,
            "username": result.username,
            "email": f"{result.username}@example.com",  # Mock email
            "role": result.roles[0] if result.roles else "user",
            "roles": result.roles,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def verify_staff_access(current_user: dict = Depends(get_current_user)) -> None:
    """FastAPI dependency to verify staff access."""
    staff_roles = ["admin", "manager", "support"]
    user_role = current_user.get("role", "")

    if user_role not in staff_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Staff access required"
        )


def require_admin_access(current_user: dict = Depends(get_current_user)) -> None:
    """FastAPI dependency to require admin access."""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )
