"""Common utilities and shared components."""

# Core utilities
from .logging import get_logger
from .settings import (
    BaseServiceSettings,
    get_service_config,
    validate_required_env_vars,
)
from .health_check import (
    health,
    detailed_health,
    get_health_checker,
    register_health_check,
)
from .metrics import get_metrics_collector, record_request, get_metrics_output
from .database import DatabaseManager, get_connection
from .redis_client import get_redis, get_redis_connection
from .consul_client import register_service

# Advanced utilities
from .auth import AuthManager, get_auth_manager, authenticate, authenticate_request
from .caching import CacheManager, get_cache_manager, cached
from .exceptions import (
    ServiceError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    ResourceNotFoundError,
    ExternalServiceError,
    service_error_to_http_exception,
    handle_common_exceptions,
)
from .validation import (
    validate_required_fields,
    validate_string_length,
    validate_email,
    validate_uuid,
    validate_path,
    ValidationSchema,
)
from .utils import (
    generate_id,
    generate_hash,
    safe_json_loads,
    safe_json_dumps,
    flatten_dict,
    format_bytes,
    format_duration,
    Timer,
    RateLimiter,
)

__all__ = [
    # Core
    "get_logger",
    "BaseServiceSettings",
    "get_service_config",
    "validate_required_env_vars",
    "health",
    "detailed_health",
    "get_health_checker",
    "register_health_check",
    "get_metrics_collector",
    "record_request",
    "get_metrics_output",
    "DatabaseManager",
    "get_connection",
    "get_redis",
    "get_redis_connection",
    "register_service",
    # Advanced
    "AuthManager",
    "get_auth_manager",
    "authenticate",
    "authenticate_request",
    "CacheManager",
    "get_cache_manager",
    "cached",
    "ServiceError",
    "ValidationError",
    "AuthenticationError",
    "AuthorizationError",
    "ResourceNotFoundError",
    "ExternalServiceError",
    "service_error_to_http_exception",
    "handle_common_exceptions",
    "validate_required_fields",
    "validate_string_length",
    "validate_email",
    "validate_uuid",
    "validate_path",
    "ValidationSchema",
    "generate_id",
    "generate_hash",
    "safe_json_loads",
    "safe_json_dumps",
    "flatten_dict",
    "format_bytes",
    "format_duration",
    "Timer",
    "RateLimiter",
]
