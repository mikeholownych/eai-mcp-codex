"""
Comprehensive Input Validation Schemas

Provides Pydantic schemas for validating API inputs across all services.
Includes common validation patterns, security-focused validators, and
reusable schema components.
"""

import re
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, date
from enum import Enum
from uuid import UUID
import ipaddress
from urllib.parse import urlparse

from pydantic import (
    BaseModel,
    Field,
    validator,
    root_validator,
    constr,
    conint,
    conlist,
    confloat,
)
from pydantic.networks import EmailStr, HttpUrl
import os


# Common validation patterns
USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{3,50}$")
PASSWORD_PATTERN = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,128}$"
)
FILENAME_PATTERN = re.compile(r"^[a-zA-Z0-9._-]+$")
API_KEY_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{32,128}$")
SLUG_PATTERN = re.compile(r"^[a-z0-9-]+$")


class ValidationError(Exception):
    """Custom validation error"""

    pass


# Common string types with validation
SecureString = constr(min_length=1, max_length=1000, strip_whitespace=True)
Username = constr(regex=USERNAME_PATTERN, min_length=3, max_length=50)
SafeFilename = constr(regex=FILENAME_PATTERN, min_length=1, max_length=255)
APIKey = constr(regex=API_KEY_PATTERN, min_length=32, max_length=128)
Slug = constr(regex=SLUG_PATTERN, min_length=1, max_length=100)

# Numeric constraints
PositiveInt = conint(ge=1)
NonNegativeInt = conint(ge=0)
LimitedInt = conint(ge=1, le=1000)
PortNumber = conint(ge=1, le=65535)


class UserRole(str, Enum):
    """User role enumeration"""

    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"
    DEVELOPER = "developer"
    SECURITY = "security"


class ServiceName(str, Enum):
    """Service name enumeration"""

    MODEL_ROUTER = "model_router"
    PLAN_MANAGEMENT = "plan_management"
    GIT_WORKTREE = "git_worktree"
    WORKFLOW_ORCHESTRATOR = "workflow_orchestrator"
    VERIFICATION_FEEDBACK = "verification_feedback"


class BaseSecureModel(BaseModel):
    """Base model with security-focused validation"""

    class Config:
        # Prevent extra fields
        extra = "forbid"
        # Validate assignments
        validate_assignment = True
        # Use enum values
        use_enum_values = True
        # JSON encoders for special types
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }

    @validator("*", pre=True)
    def prevent_null_bytes(cls, v):
        """Prevent null byte injection"""
        if isinstance(v, str) and "\x00" in v:
            raise ValueError("Null bytes not allowed")
        return v


# Authentication & Authorization Schemas
class LoginRequest(BaseSecureModel):
    """User login request"""

    username: Username
    password: constr(min_length=1, max_length=128)
    remember_me: bool = False

    @validator("password")
    def validate_password_complexity(cls, v):
        """Validate password meets security requirements"""
        if not PASSWORD_PATTERN.match(v):
            raise ValueError(
                "Password must be 8-128 characters with uppercase, lowercase, digit, and special character"
            )
        return v


class TokenRequest(BaseSecureModel):
    """Token request/refresh"""

    grant_type: constr(regex=r"^(password|refresh_token|client_credentials)$")
    username: Optional[Username] = None
    password: Optional[str] = None
    refresh_token: Optional[constr(min_length=32, max_length=512)] = None
    scope: Optional[constr(max_length=200)] = None


class UserRegistration(BaseSecureModel):
    """User registration schema"""

    username: Username
    email: EmailStr
    password: constr(min_length=8, max_length=128)
    full_name: Optional[constr(min_length=1, max_length=100)] = None
    role: UserRole = UserRole.USER

    @validator("password")
    def validate_password_strength(cls, v):
        if not PASSWORD_PATTERN.match(v):
            raise ValueError("Password does not meet security requirements")
        return v

    @root_validator
    def validate_admin_registration(cls, values):
        """Prevent unauthorized admin registration"""
        if values.get("role") == UserRole.ADMIN:
            # Only allow when explicitly enabled or during tests
            allow_env = os.getenv("ALLOW_ADMIN_REGISTRATION", "false").lower()
            testing_mode = os.getenv("TESTING_MODE", "false").lower()
            if allow_env not in {"1", "true", "yes"} and testing_mode not in {"1", "true", "yes"}:
                raise ValueError("Admin registration is not permitted")
        return values


class PasswordChangeRequest(BaseSecureModel):
    """Password change request"""

    current_password: constr(min_length=1, max_length=128)
    new_password: constr(min_length=8, max_length=128)
    confirm_password: constr(min_length=8, max_length=128)

    @validator("new_password")
    def validate_new_password(cls, v):
        if not PASSWORD_PATTERN.match(v):
            raise ValueError("New password does not meet security requirements")
        return v

    @root_validator
    def passwords_match(cls, values):
        if values.get("new_password") != values.get("confirm_password"):
            raise ValueError("Passwords do not match")
        return values


# API Request Schemas
class PaginationRequest(BaseSecureModel):
    """Pagination parameters"""

    page: conint(ge=1, le=10000) = 1
    limit: conint(ge=1, le=100) = 20
    sort_by: Optional[constr(max_length=50)] = None
    sort_order: Optional[constr(regex=r"^(asc|desc)$")] = "asc"


class SearchRequest(BaseSecureModel):
    """Search query parameters"""

    query: constr(min_length=1, max_length=500, strip_whitespace=True)
    filters: Optional[Dict[str, Any]] = None
    pagination: Optional[PaginationRequest] = None

    @validator("query")
    def validate_search_query(cls, v):
        # Prevent potential injection attacks in search
        dangerous_patterns = [
            "<script",
            "javascript:",
            "vbscript:",
            "<!--",
            "-->",
            "UNION",
            "SELECT",
        ]
        v_lower = v.lower()
        for pattern in dangerous_patterns:
            if pattern.lower() in v_lower:
                raise ValueError(
                    f"Search query contains potentially dangerous content: {pattern}"
                )
        return v

    @validator("filters")
    def validate_filters(cls, v):
        if v and len(v) > 20:
            raise ValueError("Too many filter parameters")
        return v


# File Upload Schemas
class FileUploadRequest(BaseSecureModel):
    """File upload validation"""

    filename: SafeFilename
    content_type: constr(max_length=100)
    size: conint(ge=1, le=100_000_000)  # Max 100MB
    checksum: Optional[constr(min_length=32, max_length=128)] = None

    @validator("filename")
    def validate_file_extension(cls, v):
        """Validate file extension is allowed"""
        allowed_extensions = {
            ".txt",
            ".md",
            ".json",
            ".yml",
            ".yaml",
            ".py",
            ".js",
            ".ts",
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".pdf",
            ".zip",
            ".tar.gz",
        }

        # Get file extension
        parts = v.lower().split(".")
        if len(parts) < 2:
            raise ValueError("File must have an extension")

        ext = "." + parts[-1]
        if ext not in allowed_extensions:
            raise ValueError(f"File extension {ext} not allowed")

        return v

    @validator("content_type")
    def validate_content_type(cls, v):
        """Validate content type matches expectations"""
        allowed_types = {
            "text/plain",
            "text/markdown",
            "application/json",
            "application/yaml",
            "text/x-python",
            "application/javascript",
            "application/typescript",
            "image/jpeg",
            "image/png",
            "image/gif",
            "application/pdf",
            "application/zip",
            "application/gzip",
        }

        if v not in allowed_types:
            raise ValueError(f"Content type {v} not allowed")

        return v


# Model Router Schemas
class ModelRequest(BaseSecureModel):
    """AI model request"""

    model: constr(regex=r"^(claude-3|gpt-4|gemini).*$", max_length=50)
    prompt: constr(min_length=1, max_length=50000)
    max_tokens: Optional[conint(ge=1, le=8192)] = None
    temperature: Optional[confloat(ge=0.0, le=2.0)] = None
    top_p: Optional[confloat(ge=0.0, le=1.0)] = None
    stream: bool = False
    metadata: Optional[Dict[str, Any]] = None

    @validator("prompt")
    def validate_prompt_content(cls, v):
        """Check for potentially harmful prompt content"""
        # Basic checks for prompt injection attempts
        dangerous_patterns = [
            "ignore previous instructions",
            "forget everything above",
            "system prompt",
            "new instructions:",
        ]

        v_lower = v.lower()
        for pattern in dangerous_patterns:
            if pattern in v_lower:
                raise ValueError("Prompt contains potentially dangerous content")

        return v

    @validator("metadata")
    def validate_metadata_size(cls, v):
        if v and len(str(v)) > 10000:
            raise ValueError("Metadata too large")
        return v


class ModelResponse(BaseSecureModel):
    """AI model response"""

    model: str
    response: str
    usage: Dict[str, int]
    metadata: Optional[Dict[str, Any]] = None


# Git Operations Schemas
class GitRepositoryRequest(BaseSecureModel):
    """Git repository operation request"""

    repository_url: HttpUrl
    branch: Optional[constr(regex=r"^[a-zA-Z0-9/_-]+$", max_length=100)] = "main"
    commit_hash: Optional[constr(regex=r"^[a-f0-9]{7,40}$")] = None
    path: Optional[constr(max_length=500)] = None

    @validator("repository_url")
    def validate_repository_url(cls, v):
        """Validate repository URL is from allowed sources"""
        allowed_hosts = ["github.com", "gitlab.com", "bitbucket.org"]
        parsed = urlparse(str(v))

        if parsed.hostname not in allowed_hosts:
            raise ValueError(f"Repository host {parsed.hostname} not allowed")

        return v

    @validator("path")
    def validate_path_safety(cls, v):
        """Prevent path traversal attacks"""
        if v and (".." in v or v.startswith("/")):
            raise ValueError("Invalid path: path traversal detected")
        return v


class CommitRequest(BaseSecureModel):
    """Git commit request"""

    message: constr(min_length=1, max_length=500)
    files: conlist(str, min_items=1, max_items=50)
    author_name: Optional[constr(max_length=100)] = None
    author_email: Optional[EmailStr] = None

    @validator("files", each_item=True)
    def validate_file_paths(cls, v):
        """Validate file paths are safe"""
        if ".." in v or v.startswith("/"):
            raise ValueError(f"Unsafe file path: {v}")
        return v


# Plan Management Schemas
class TaskRequest(BaseSecureModel):
    """Task creation/update request"""

    title: constr(min_length=1, max_length=200)
    description: Optional[constr(max_length=5000)] = None
    priority: constr(regex=r"^(low|medium|high|critical)$") = "medium"
    assignee: Optional[Username] = None
    due_date: Optional[datetime] = None
    tags: Optional[conlist(str, max_items=10)] = None
    metadata: Optional[Dict[str, Any]] = None

    @validator("tags", each_item=True)
    def validate_tags(cls, v):
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError(f"Invalid tag format: {v}")
        return v


class PlanRequest(BaseSecureModel):
    """Project plan request"""

    name: constr(min_length=1, max_length=100)
    description: Optional[constr(max_length=1000)] = None
    repository_url: Optional[HttpUrl] = None
    target_date: Optional[date] = None
    tasks: Optional[List[TaskRequest]] = None

    @validator("tasks")
    def validate_task_count(cls, v):
        if v and len(v) > 100:
            raise ValueError("Too many tasks in plan")
        return v


# Workflow Orchestrator Schemas
class WorkflowRequest(BaseSecureModel):
    """Workflow execution request"""

    workflow_name: constr(regex=r"^[a-zA-Z0-9_-]+$", max_length=50)
    parameters: Optional[Dict[str, Any]] = None
    priority: constr(regex=r"^(low|normal|high)$") = "normal"
    timeout: Optional[conint(ge=1, le=3600)] = None  # Max 1 hour

    @validator("parameters")
    def validate_parameters(cls, v):
        """Validate workflow parameters"""
        if v:
            # Check parameter count and size
            if len(v) > 50:
                raise ValueError("Too many workflow parameters")

            # Check total size
            if len(str(v)) > 50000:
                raise ValueError("Workflow parameters too large")

        return v


class ServiceHealthRequest(BaseSecureModel):
    """Service health check request"""

    service: ServiceName
    detailed: bool = False


# Verification & Feedback Schemas
class CodeReviewRequest(BaseSecureModel):
    """Code review request"""

    code: constr(min_length=1, max_length=100000)
    language: constr(regex=r"^(python|javascript|typescript|java|go|rust|c|cpp)$")
    context: Optional[constr(max_length=5000)] = None
    check_security: bool = True
    check_performance: bool = True
    check_style: bool = True


class FeedbackRequest(BaseSecureModel):
    """User feedback request"""

    type: constr(regex=r"^(bug|feature|improvement|security)$")
    title: constr(min_length=1, max_length=200)
    description: constr(min_length=10, max_length=5000)
    severity: constr(regex=r"^(low|medium|high|critical)$") = "medium"
    reproduction_steps: Optional[constr(max_length=2000)] = None
    environment: Optional[Dict[str, str]] = None


# System Configuration Schemas
class ConfigurationUpdate(BaseSecureModel):
    """System configuration update"""

    service: ServiceName
    config_key: constr(regex=r"^[a-zA-Z0-9._-]+$", max_length=100)
    config_value: Union[str, int, float, bool, List[Any], Dict[str, Any]]

    @validator("config_value")
    def validate_config_value(cls, v):
        """Validate configuration value is safe"""
        if isinstance(v, str):
            # Check for potentially dangerous values
            dangerous_patterns = ["password", "secret", "key", "token"]
            key_lower = str(v).lower()
            for pattern in dangerous_patterns:
                if pattern in key_lower and len(str(v)) > 20:
                    raise ValueError(
                        "Configuration value appears to contain sensitive data"
                    )

        return v


# Network and Security Schemas
class IPWhitelistRequest(BaseSecureModel):
    """IP whitelist management"""

    ip_address: Union[
        ipaddress.IPv4Address,
        ipaddress.IPv6Address,
        ipaddress.IPv4Network,
        ipaddress.IPv6Network,
    ]
    description: Optional[constr(max_length=200)] = None
    expires_at: Optional[datetime] = None


class APIKeyRequest(BaseSecureModel):
    """API key generation request"""

    name: constr(min_length=1, max_length=100)
    description: Optional[constr(max_length=500)] = None
    permissions: List[constr(regex=r"^[a-z_]+$")] = []
    expires_at: Optional[datetime] = None

    @validator("permissions")
    def validate_permissions(cls, v):
        if len(v) > 20:
            raise ValueError("Too many permissions requested")
        return v


# Response Schemas
class ErrorResponse(BaseSecureModel):
    """Standard error response"""

    error: str
    message: str
    code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SuccessResponse(BaseSecureModel):
    """Standard success response"""

    success: bool = True
    message: str
    data: Optional[Any] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Schema registry for dynamic validation
SCHEMA_REGISTRY = {
    "auth.login": LoginRequest,
    "auth.register": UserRegistration,
    "auth.password_change": PasswordChangeRequest,
    "files.upload": FileUploadRequest,
    "models.request": ModelRequest,
    "git.repository": GitRepositoryRequest,
    "git.commit": CommitRequest,
    "tasks.request": TaskRequest,
    "plans.request": PlanRequest,
    "workflows.request": WorkflowRequest,
    "code.review": CodeReviewRequest,
    "feedback.request": FeedbackRequest,
    "config.update": ConfigurationUpdate,
    "security.ip_whitelist": IPWhitelistRequest,
    "security.api_key": APIKeyRequest,
}


def get_schema(schema_name: str) -> Optional[BaseModel]:
    """Get schema by name from registry"""
    return SCHEMA_REGISTRY.get(schema_name)


def validate_request(schema_name: str, data: Dict[str, Any]) -> BaseModel:
    """Validate request data against schema"""
    schema_class = get_schema(schema_name)
    if not schema_class:
        raise ValidationError(f"Schema '{schema_name}' not found")

    try:
        return schema_class(**data)
    except Exception as e:
        raise ValidationError(f"Validation failed: {str(e)}")


# Utility validators
def validate_json_size(v: Any, max_size: int = 1000000) -> Any:
    """Validate JSON object size"""
    import json

    if len(json.dumps(v, default=str)) > max_size:
        raise ValueError(f"JSON object too large (max {max_size} bytes)")
    return v


def validate_no_html(v: str) -> str:
    """Ensure string contains no HTML"""
    if "<" in v and ">" in v:
        raise ValueError("HTML content not allowed")
    return v


def validate_alphanumeric_only(v: str) -> str:
    """Ensure string is alphanumeric only"""
    if not re.match(r"^[a-zA-Z0-9]+$", v):
        raise ValueError("Only alphanumeric characters allowed")
    return v
