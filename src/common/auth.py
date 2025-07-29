"""Authentication and authorization utilities."""

import hashlib
import hmac
import secrets
import time
import jwt
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

from .logging import get_logger

logger = get_logger("auth")


class UserRole(str, Enum):
    """User role enumeration."""
    ADMIN = "admin"
    USER = "user"
    SERVICE = "service"
    READONLY = "readonly"


@dataclass
class AuthToken:
    """Authentication token information."""
    user_id: str
    username: str
    roles: List[str]
    expires_at: datetime
    issued_at: datetime
    token_type: str = "bearer"


@dataclass 
class AuthResult:
    """Authentication result."""
    success: bool
    user_id: Optional[str] = None
    username: Optional[str] = None
    roles: List[str] = None
    error_message: Optional[str] = None
    token_info: Optional[AuthToken] = None


class AuthManager:
    """Enhanced authentication manager."""
    
    def __init__(self, secret_key: str = None, token_expiry_hours: int = 24):
        self.secret_key = secret_key or secrets.token_urlsafe(32)
        self.token_expiry_hours = token_expiry_hours
        self.algorithm = "HS256"
        
        # In-memory user store (in production, this would be a database)
        self._users = {}
        self._api_keys = {}
        self._revoked_tokens = set()
        
        # Initialize with default admin user
        self._create_default_users()
    
    def _create_default_users(self):
        """Create default users for testing."""
        self._users = {
            "admin": {
                "user_id": "admin",
                "username": "admin", 
                "password_hash": self._hash_password("admin123"),
                "roles": [UserRole.ADMIN.value],
                "is_active": True,
                "created_at": datetime.utcnow()
            },
            "service": {
                "user_id": "service",
                "username": "service",
                "password_hash": self._hash_password("service123"),
                "roles": [UserRole.SERVICE.value],
                "is_active": True,
                "created_at": datetime.utcnow()
            }
        }
        
        # Create default API keys
        self._api_keys = {
            "test-api-key-123": {
                "user_id": "service",
                "username": "service",
                "roles": [UserRole.SERVICE.value],
                "created_at": datetime.utcnow(),
                "last_used": None
            }
        }
    
    def _hash_password(self, password: str) -> str:
        """Hash a password using PBKDF2."""
        salt = secrets.token_bytes(32)
        pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return salt.hex() + pwdhash.hex()
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password against its hash."""
        try:
            salt = bytes.fromhex(password_hash[:64])
            stored_hash = bytes.fromhex(password_hash[64:])
            pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
            return hmac.compare_digest(stored_hash, pwdhash)
        except ValueError:
            return False
    
    def create_user(self, username: str, password: str, roles: List[str] = None) -> bool:
        """Create a new user."""
        if username in self._users:
            logger.warning(f"User {username} already exists")
            return False
        
        user_id = secrets.token_urlsafe(16)
        self._users[username] = {
            "user_id": user_id,
            "username": username,
            "password_hash": self._hash_password(password),
            "roles": roles or [UserRole.USER.value],
            "is_active": True,
            "created_at": datetime.utcnow(),
            "last_login": None
        }
        
        logger.info(f"Created user: {username}")
        return True
    
    def authenticate_password(self, username: str, password: str) -> AuthResult:
        """Authenticate user with username and password."""
        user = self._users.get(username)
        if not user:
            return AuthResult(success=False, error_message="User not found")
        
        if not user.get("is_active", True):
            return AuthResult(success=False, error_message="User account is disabled")
        
        if not self._verify_password(password, user["password_hash"]):
            return AuthResult(success=False, error_message="Invalid password")
        
        # Update last login
        user["last_login"] = datetime.utcnow()
        
        return AuthResult(
            success=True,
            user_id=user["user_id"],
            username=user["username"],
            roles=user["roles"]
        )
    
    def authenticate_api_key(self, api_key: str) -> AuthResult:
        """Authenticate using API key."""
        key_info = self._api_keys.get(api_key)
        if not key_info:
            return AuthResult(success=False, error_message="Invalid API key")
        
        # Update last used
        key_info["last_used"] = datetime.utcnow()
        
        return AuthResult(
            success=True,
            user_id=key_info["user_id"],
            username=key_info["username"], 
            roles=key_info["roles"]
        )
    
    def create_jwt_token(self, user_id: str, username: str, roles: List[str]) -> str:
        """Create a JWT token."""
        now = datetime.utcnow()
        expires_at = now + timedelta(hours=self.token_expiry_hours)
        
        payload = {
            "user_id": user_id,
            "username": username,
            "roles": roles,
            "iat": now,
            "exp": expires_at,
            "jti": secrets.token_urlsafe(16)  # JWT ID for revocation
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        logger.info(f"Created JWT token for user: {username}")
        return token
    
    def verify_jwt_token(self, token: str) -> AuthResult:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Check if token is revoked
            jti = payload.get("jti")
            if jti in self._revoked_tokens:
                return AuthResult(success=False, error_message="Token has been revoked")
            
            token_info = AuthToken(
                user_id=payload["user_id"],
                username=payload["username"],
                roles=payload["roles"], 
                issued_at=datetime.fromtimestamp(payload["iat"]),
                expires_at=datetime.fromtimestamp(payload["exp"])
            )
            
            return AuthResult(
                success=True,
                user_id=payload["user_id"],
                username=payload["username"],
                roles=payload["roles"],
                token_info=token_info
            )
            
        except jwt.ExpiredSignatureError:
            return AuthResult(success=False, error_message="Token has expired")
        except jwt.InvalidTokenError as e:
            return AuthResult(success=False, error_message=f"Invalid token: {str(e)}")
    
    def revoke_token(self, token: str) -> bool:
        """Revoke a JWT token.""" 
        try:
            # Decode without verification to get JTI
            payload = jwt.decode(token, options={"verify_signature": False})
            jti = payload.get("jti")
            if jti:
                self._revoked_tokens.add(jti)
                logger.info(f"Revoked token with JTI: {jti}")
                return True
        except Exception as e:
            logger.error(f"Failed to revoke token: {e}")
        
        return False
    
    def check_permission(self, user_roles: List[str], required_role: str) -> bool:
        """Check if user has required permission."""
        if UserRole.ADMIN.value in user_roles:
            return True  # Admin has all permissions
        
        return required_role in user_roles
    
    def get_user_info(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user information."""
        user = self._users.get(username)
        if user:
            # Return safe user info (no password hash)
            return {
                "user_id": user["user_id"],
                "username": user["username"],
                "roles": user["roles"],
                "is_active": user["is_active"],
                "created_at": user["created_at"].isoformat(),
                "last_login": user["last_login"].isoformat() if user["last_login"] else None
            }
        return None
    
    def create_api_key(self, username: str) -> Optional[str]:
        """Create a new API key for a user."""
        user = self._users.get(username)
        if not user:
            return None
        
        api_key = f"mcp-{secrets.token_urlsafe(32)}"
        self._api_keys[api_key] = {
            "user_id": user["user_id"],
            "username": username,
            "roles": user["roles"],
            "created_at": datetime.utcnow(),
            "last_used": None
        }
        
        logger.info(f"Created API key for user: {username}")
        return api_key
    
    def list_api_keys(self, username: str) -> List[Dict[str, Any]]:
        """List API keys for a user."""
        keys = []
        for api_key, key_info in self._api_keys.items():
            if key_info["username"] == username:
                keys.append({
                    "key_prefix": api_key[:12] + "...",
                    "created_at": key_info["created_at"].isoformat(),
                    "last_used": key_info["last_used"].isoformat() if key_info["last_used"] else None
                })
        return keys
    
    def revoke_api_key(self, api_key: str) -> bool:
        """Revoke an API key."""
        if api_key in self._api_keys:
            del self._api_keys[api_key]
            logger.info(f"Revoked API key: {api_key[:12]}...")
            return True
        return False


# Global auth manager instance
_auth_manager: Optional[AuthManager] = None


def get_auth_manager() -> AuthManager:
    """Get the global auth manager instance."""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthManager()
    return _auth_manager


def authenticate(token: str) -> bool:
    """Simple token authentication (legacy compatibility)."""
    if not token:
        return False
    
    auth_manager = get_auth_manager()
    
    # Try JWT token first
    if token.count('.') == 2:  # JWT has 3 parts separated by dots
        result = auth_manager.verify_jwt_token(token)
        return result.success
    
    # Try API key
    result = auth_manager.authenticate_api_key(token)
    return result.success


def authenticate_request(authorization_header: str) -> AuthResult:
    """Authenticate a request from Authorization header."""
    if not authorization_header:
        return AuthResult(success=False, error_message="No authorization header")
    
    auth_manager = get_auth_manager()
    
    # Parse authorization header
    parts = authorization_header.split()
    if len(parts) != 2:
        return AuthResult(success=False, error_message="Invalid authorization header format")
    
    scheme, token = parts
    
    if scheme.lower() == "bearer":
        # JWT token
        return auth_manager.verify_jwt_token(token)
    elif scheme.lower() == "apikey":
        # API key
        return auth_manager.authenticate_api_key(token)
    else:
        return AuthResult(success=False, error_message="Unsupported authorization scheme")


def require_role(required_role: str):
    """Decorator to require specific role for endpoint access."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # This would typically extract auth info from request context
            # For now, just pass through (would be implemented in FastAPI dependency)
            return func(*args, **kwargs)
        return wrapper
    return decorator


def create_service_token(service_name: str) -> str:
    """Create a service-to-service authentication token."""
    auth_manager = get_auth_manager()
    return auth_manager.create_jwt_token(
        user_id=f"service-{service_name}",
        username=service_name,
        roles=[UserRole.SERVICE.value]
    )


def validate_service_token(token: str) -> bool:
    """Validate a service-to-service token."""
    auth_manager = get_auth_manager()
    result = auth_manager.verify_jwt_token(token)
    return result.success and UserRole.SERVICE.value in (result.roles or [])


class SecurityUtils:
    """Additional security utilities."""
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate a cryptographically secure random token."""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def constant_time_compare(a: str, b: str) -> bool:
        """Constant-time string comparison to prevent timing attacks."""
        return hmac.compare_digest(a.encode(), b.encode())
    
    @staticmethod
    def hash_sensitive_data(data: str) -> str:
        """Hash sensitive data for logging/storage."""
        return hashlib.sha256(data.encode()).hexdigest()[:16] + "..."
    
    @staticmethod
    def validate_token_format(token: str) -> bool:
        """Validate basic token format requirements."""
        if not token or len(token) < 16:
            return False
        
        # Check for common patterns
        if token.startswith(('test', 'debug', 'temp')):
            logger.warning("Potentially insecure token detected")
            
        return True
    
    @staticmethod
    def get_request_fingerprint(user_agent: str = "", ip_address: str = "") -> str:
        """Generate a request fingerprint for rate limiting/security."""
        fingerprint_data = f"{user_agent}:{ip_address}:{int(time.time() // 3600)}"
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()[:16]
