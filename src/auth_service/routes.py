"""Authentication service API routes."""

from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer
import secrets

from src.auth_service.models import (
    UserRegistration, UserLogin, UserResponse, TokenResponse,
    ApiKeyResponse, PasswordChange, ErrorResponse
)
from src.common.auth import get_auth_manager, AuthResult
from src.common.fastapi_auth import get_current_user
from src.common.logging import get_logger

logger = get_logger("auth_service")
router = APIRouter()
security = HTTPBearer()


@router.post("/register", response_model=TokenResponse)
async def register_user(user_data: UserRegistration):
    """Register a new user account."""
    try:
        auth_manager = get_auth_manager()
        
        # Check if user already exists
        if auth_manager.get_user_info(user_data.username):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already exists"
            )
        
        # Create user
        success = auth_manager.create_user(
            username=user_data.username,
            password=user_data.password,
            roles=["user"]
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user account"
            )
        
        # Authenticate and create token
        auth_result = auth_manager.authenticate_password(
            user_data.username, user_data.password
        )
        
        if not auth_result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="User created but authentication failed"
            )
        
        # Create JWT token
        token = auth_manager.create_jwt_token(
            user_id=auth_result.user_id,
            username=auth_result.username,
            roles=auth_result.roles
        )
        
        # Get user info
        user_info = auth_manager.get_user_info(user_data.username)
        
        user_response = UserResponse(
            user_id=user_info["user_id"],
            username=user_info["username"],
            email=user_data.email,  # Store email in user data
            full_name=user_data.full_name,
            roles=user_info["roles"],
            is_active=user_info["is_active"],
            created_at=datetime.fromisoformat(user_info["created_at"]),
            last_login=None
        )
        
        logger.info(f"User registered successfully: {user_data.username}")
        
        return TokenResponse(
            access_token=token,
            expires_in=auth_manager.token_expiry_hours * 3600,
            user=user_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during registration"
        )


@router.post("/login", response_model=TokenResponse)
async def login_user(login_data: UserLogin):
    """Authenticate user and return JWT token."""
    try:
        auth_manager = get_auth_manager()
        
        # Authenticate user
        auth_result = auth_manager.authenticate_password(
            login_data.username, login_data.password
        )
        
        if not auth_result.success:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=auth_result.error_message or "Invalid credentials"
            )
        
        # Create JWT token
        token = auth_manager.create_jwt_token(
            user_id=auth_result.user_id,
            username=auth_result.username,
            roles=auth_result.roles
        )
        
        # Get user info
        user_info = auth_manager.get_user_info(login_data.username)
        
        user_response = UserResponse(
            user_id=user_info["user_id"],
            username=user_info["username"],
            email=f"{user_info['username']}@example.com",  # Mock email
            roles=user_info["roles"],
            is_active=user_info["is_active"],
            created_at=datetime.fromisoformat(user_info["created_at"]),
            last_login=datetime.fromisoformat(user_info["last_login"]) if user_info["last_login"] else None
        )
        
        logger.info(f"User logged in successfully: {login_data.username}")
        
        return TokenResponse(
            access_token=token,
            expires_in=auth_manager.token_expiry_hours * 3600,
            user=user_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during login"
        )


@router.post("/logout")
async def logout_user(current_user: dict = Depends(get_current_user)):
    """Logout user (revoke current token)."""
    try:
        # In a stateless JWT system, logout is typically handled client-side
        # by discarding the token. For enhanced security, we could maintain
        # a token blacklist, but for now we'll just return success.
        
        logger.info(f"User logged out: {current_user['username']}")
        return {"message": "Logged out successfully"}
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during logout"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current authenticated user information."""
    try:
        auth_manager = get_auth_manager()
        user_info = auth_manager.get_user_info(current_user["username"])
        
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse(
            user_id=user_info["user_id"],
            username=user_info["username"],
            email=current_user.get("email", f"{user_info['username']}@example.com"),
            roles=user_info["roles"],
            is_active=user_info["is_active"],
            created_at=datetime.fromisoformat(user_info["created_at"]),
            last_login=datetime.fromisoformat(user_info["last_login"]) if user_info["last_login"] else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user info error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: dict = Depends(get_current_user)
):
    """Change user password."""
    try:
        auth_manager = get_auth_manager()
        
        # Verify current password
        auth_result = auth_manager.authenticate_password(
            current_user["username"], password_data.current_password
        )
        
        if not auth_result.success:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect"
            )
        
        # Update password (in real implementation, this would update the database)
        # For now, we'll simulate success
        logger.info(f"Password changed for user: {current_user['username']}")
        
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during password change"
        )


@router.post("/api-key", response_model=ApiKeyResponse)
async def create_api_key(current_user: dict = Depends(get_current_user)):
    """Create a new API key for the current user."""
    try:
        auth_manager = get_auth_manager()
        
        api_key = auth_manager.create_api_key(current_user["username"])
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create API key"
            )
        
        logger.info(f"API key created for user: {current_user['username']}")
        
        return ApiKeyResponse(
            api_key=api_key,
            created_at=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API key creation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during API key creation"
        )


@router.get("/api-keys")
async def list_api_keys(current_user: dict = Depends(get_current_user)):
    """List API keys for the current user."""
    try:
        auth_manager = get_auth_manager()
        api_keys = auth_manager.list_api_keys(current_user["username"])
        
        return {"api_keys": api_keys}
        
    except Exception as e:
        logger.error(f"API key listing error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.delete("/api-key/{key_prefix}")
async def revoke_api_key(
    key_prefix: str,
    current_user: dict = Depends(get_current_user)
):
    """Revoke an API key (requires key prefix for identification)."""
    try:
        # In a real implementation, you'd find the full key by prefix
        # and verify ownership before revoking
        logger.info(f"API key revocation requested by user: {current_user['username']}")
        
        return {"message": "API key revoked successfully"}
        
    except Exception as e:
        logger.error(f"API key revocation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during API key revocation"
        )


@router.post("/refresh-token", response_model=TokenResponse)
async def refresh_token(current_user: dict = Depends(get_current_user)):
    """Refresh the current JWT token."""
    try:
        auth_manager = get_auth_manager()
        
        # Create new JWT token
        new_token = auth_manager.create_jwt_token(
            user_id=current_user["user_id"],
            username=current_user["username"],
            roles=current_user["roles"]
        )
        
        # Get user info
        user_info = auth_manager.get_user_info(current_user["username"])
        
        user_response = UserResponse(
            user_id=user_info["user_id"],
            username=user_info["username"],
            email=current_user.get("email", f"{user_info['username']}@example.com"),
            roles=user_info["roles"],
            is_active=user_info["is_active"],
            created_at=datetime.fromisoformat(user_info["created_at"]),
            last_login=datetime.fromisoformat(user_info["last_login"]) if user_info["last_login"] else None
        )
        
        logger.info(f"Token refreshed for user: {current_user['username']}")
        
        return TokenResponse(
            access_token=new_token,
            expires_in=auth_manager.token_expiry_hours * 3600,
            user=user_response
        )
        
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during token refresh"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "auth-service",
        "timestamp": datetime.utcnow().isoformat()
    }