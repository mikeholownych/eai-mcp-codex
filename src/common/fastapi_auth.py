"""FastAPI authentication dependencies."""

from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .auth import get_auth_manager

security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """FastAPI dependency to get current user from JWT token."""
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
        "roles": result.roles
    }


def verify_staff_access(current_user: dict = Depends(get_current_user)) -> None:
    """FastAPI dependency to verify staff access."""
    staff_roles = ["admin", "manager", "support"]
    user_role = current_user.get("role", "")
    
    if user_role not in staff_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff access required"
        )


def require_admin_access(current_user: dict = Depends(get_current_user)) -> None:
    """FastAPI dependency to require admin access."""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )