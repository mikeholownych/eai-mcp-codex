"""
Security Middleware Integration

Combines all Tier 2 security components into a comprehensive security middleware stack.
Provides easy integration with FastAPI applications and configurable security layers.
"""

from typing import Optional, List
from fastapi import FastAPI
from fastapi.middleware.base import BaseHTTPMiddleware
import logging

from .config import SecurityConfigManager, get_security_config
from .rate_limiting import RateLimiter, RateLimitMiddleware, setup_rate_limiter
from .validation import (
    ValidationMiddleware,
    ValidationConfig,
    create_validation_middleware,
)
from .headers import (
    SecurityHeadersMiddleware,
    SecurityHeadersConfig,
    create_security_headers_middleware,
)
from .audit_logging import AuditLogger, AuditMiddleware, get_audit_logger
from ..common.redis_client import RedisClient
from ..common.settings import BaseServiceSettings

logger = logging.getLogger(__name__)


class SecurityMiddlewareStack:
    """
    Comprehensive security middleware stack that combines all security components
    """

    def __init__(
        self,
        app: FastAPI,
        redis_client: Optional[RedisClient] = None,
        settings: Optional[BaseServiceSettings] = None,
        config_manager: Optional[SecurityConfigManager] = None,
    ):

        self.app = app
        self.redis_client = redis_client
        self.settings = settings or BaseServiceSettings()
        self.config_manager = config_manager or get_security_config()

        # Initialize components
        self.rate_limiter: Optional[RateLimiter] = None
        self.audit_logger: Optional[AuditLogger] = None
        self.validation_middleware: Optional[ValidationMiddleware] = None
        self.headers_middleware: Optional[SecurityHeadersMiddleware] = None

        # Middleware instances
        self._middlewares: List[BaseHTTPMiddleware] = []

    async def initialize(self):
        """Initialize all security components"""
        try:
            # Initialize rate limiter
            if self.config_manager.config.rate_limiting.enabled and self.redis_client:
                self.rate_limiter = await setup_rate_limiter(
                    self.redis_client, self.settings
                )
                logger.info("Rate limiting initialized")

            # Initialize audit logger
            if self.config_manager.config.audit.enabled:
                self.audit_logger = get_audit_logger()
                logger.info("Audit logging initialized")

            # Initialize validation middleware
            if self.config_manager.config.validation.enabled:
                validation_config = ValidationConfig(
                    max_string_length=self.config_manager.config.validation.max_string_length,
                    max_array_length=self.config_manager.config.validation.max_array_length,
                    max_object_depth=self.config_manager.config.validation.max_object_depth,
                    block_sql_keywords=self.config_manager.config.validation.block_sql_keywords,
                    block_script_tags=self.config_manager.config.validation.block_script_tags,
                    normalize_unicode=self.config_manager.config.validation.normalize_unicode,
                    validate_json_structure=self.config_manager.config.validation.validate_json_structure,
                )
                self.validation_middleware = create_validation_middleware(
                    validation_config
                )
                logger.info("Input validation initialized")

            # Initialize security headers middleware
            headers_config = SecurityHeadersConfig()
            headers_config.csp_default_src = self.config_manager.config.csp.default_src
            headers_config.csp_script_src = self.config_manager.config.csp.script_src
            headers_config.csp_style_src = self.config_manager.config.csp.style_src
            headers_config.csp_img_src = self.config_manager.config.csp.img_src
            headers_config.x_frame_options = (
                self.config_manager.config.headers.x_frame_options
            )
            headers_config.hsts_max_age = (
                self.config_manager.config.headers.hsts_max_age
            )
            headers_config.cors_allow_origins = (
                self.config_manager.config.cors.allow_origins
            )
            headers_config.cors_allow_methods = (
                self.config_manager.config.cors.allow_methods
            )
            headers_config.cors_allow_headers = (
                self.config_manager.config.cors.allow_headers
            )
            headers_config.csrf_protection_enabled = True

            self.headers_middleware = create_security_headers_middleware(headers_config)
            logger.info("Security headers initialized")

            logger.info("Security middleware stack initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize security middleware stack: {e}")
            raise

    def add_to_app(self):
        """Add all security middleware to the FastAPI app"""
        try:
            # Add middleware in reverse order (last added = first executed)

            # 1. Audit logging (should be outermost to catch all requests)
            if self.audit_logger:
                audit_middleware = AuditMiddleware(self.audit_logger)
                self.app.middleware("http")(audit_middleware)
                logger.info("Added audit logging middleware")

            # 2. Security headers (should be early to set security headers)
            if self.headers_middleware:
                self.app.middleware("http")(self.headers_middleware)
                logger.info("Added security headers middleware")

            # 3. Rate limiting (should be early to block excessive requests)
            if self.rate_limiter:
                rate_limit_middleware = RateLimitMiddleware(self.rate_limiter)
                self.app.middleware("http")(rate_limit_middleware)
                logger.info("Added rate limiting middleware")

            # 4. Input validation (should be before business logic)
            if self.validation_middleware:
                self.app.middleware("http")(self.validation_middleware)
                logger.info("Added input validation middleware")

            logger.info("Security middleware stack added to application")

        except Exception as e:
            logger.error(f"Failed to add security middleware to app: {e}")
            raise

    def configure_endpoint_security(
        self,
        path: str,
        method: str,
        rate_limit: Optional[int] = None,
        rate_window: Optional[int] = None,
        validation_schema: Optional[str] = None,
        audit_required: bool = True,
    ):
        """Configure security for specific endpoint"""

        # Configure rate limiting for endpoint
        if self.rate_limiter and rate_limit and rate_window:
            from .rate_limiting import RateLimitStrategy

            rate_middleware = RateLimitMiddleware(self.rate_limiter)
            rate_middleware.configure_endpoint(
                path, method, rate_limit, rate_window, RateLimitStrategy.SLIDING_WINDOW
            )

        # Configure validation for endpoint
        if self.validation_middleware and validation_schema:
            from .validation import SchemaValidator

            SchemaValidator()

        logger.info(f"Configured security for {method} {path}")

    def get_security_status(self) -> dict:
        """Get current security middleware status"""
        return {
            "rate_limiting": {
                "enabled": self.rate_limiter is not None,
                "redis_connected": (
                    self.redis_client is not None if self.redis_client else False
                ),
            },
            "audit_logging": {"enabled": self.audit_logger is not None},
            "input_validation": {"enabled": self.validation_middleware is not None},
            "security_headers": {"enabled": self.headers_middleware is not None},
            "configuration": self.config_manager.get_security_summary(),
        }


class SecurityMiddlewareFactory:
    """Factory for creating security middleware configurations"""

    @staticmethod
    def create_development_stack(
        app: FastAPI,
        redis_client: Optional[RedisClient] = None,
        settings: Optional[BaseServiceSettings] = None,
    ) -> SecurityMiddlewareStack:
        """Create security stack for development environment"""
        from .config import SecurityConfigPresets, SecurityConfigManager

        config = SecurityConfigPresets.development()
        config_manager = SecurityConfigManager(config)

        return SecurityMiddlewareStack(app, redis_client, settings, config_manager)

    @staticmethod
    def create_production_stack(
        app: FastAPI, redis_client: RedisClient, settings: BaseServiceSettings
    ) -> SecurityMiddlewareStack:
        """Create security stack for production environment"""
        from .config import SecurityConfigPresets, SecurityConfigManager

        config = SecurityConfigPresets.production()
        config_manager = SecurityConfigManager(config)

        return SecurityMiddlewareStack(app, redis_client, settings, config_manager)

    @staticmethod
    def create_high_security_stack(
        app: FastAPI, redis_client: RedisClient, settings: BaseServiceSettings
    ) -> SecurityMiddlewareStack:
        """Create high-security stack for sensitive environments"""
        from .config import SecurityConfigPresets, SecurityConfigManager

        config = SecurityConfigPresets.high_security()
        config_manager = SecurityConfigManager(config)

        return SecurityMiddlewareStack(app, redis_client, settings, config_manager)


# Convenience function for easy setup
async def setup_security_middleware(
    app: FastAPI,
    environment: str = "production",
    redis_client: Optional[RedisClient] = None,
    settings: Optional[BaseServiceSettings] = None,
    custom_config: Optional[SecurityConfigManager] = None,
) -> SecurityMiddlewareStack:
    """
    Set up complete security middleware stack for a FastAPI application

    Args:
        app: FastAPI application instance
        environment: Environment type (development, production, high_security)
        redis_client: Redis client for rate limiting (optional)
        settings: Application settings (optional)
        custom_config: Custom security configuration (optional)

    Returns:
        Configured SecurityMiddlewareStack
    """

    if custom_config:
        stack = SecurityMiddlewareStack(app, redis_client, settings, custom_config)
    else:
        # Use factory based on environment
        if environment == "development":
            stack = SecurityMiddlewareFactory.create_development_stack(
                app, redis_client, settings
            )
        elif environment == "high_security":
            stack = SecurityMiddlewareFactory.create_high_security_stack(
                app, redis_client, settings
            )
        else:  # production
            stack = SecurityMiddlewareFactory.create_production_stack(
                app, redis_client, settings
            )

    # Initialize and add to app
    await stack.initialize()
    stack.add_to_app()

    logger.info(f"Security middleware stack configured for {environment} environment")

    return stack


# Decorator for securing specific routes
def secure_endpoint(
    rate_limit: Optional[int] = None,
    rate_window: Optional[int] = None,
    validation_schema: Optional[str] = None,
    audit_required: bool = True,
    admin_only: bool = False,
):
    """
    Decorator to add security configuration to specific endpoints

    Usage:
        @app.post("/api/sensitive")
        @secure_endpoint(rate_limit=10, rate_window=60, validation_schema="sensitive_data")
        async def sensitive_endpoint():
            pass
    """

    def decorator(func):
        # Store security metadata on the function
        func._security_config = {
            "rate_limit": rate_limit,
            "rate_window": rate_window,
            "validation_schema": validation_schema,
            "audit_required": audit_required,
            "admin_only": admin_only,
        }
        return func

    return decorator


# Context managers for temporary security adjustments
class SecurityContext:
    """Context manager for temporary security configuration changes"""

    def __init__(self, config_manager: SecurityConfigManager):
        self.config_manager = config_manager
        self.original_config = None

    def __enter__(self):
        # Save original configuration
        self.original_config = self.config_manager.config.copy(deep=True)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore original configuration
        if self.original_config:
            self.config_manager.config = self.original_config

    def temporarily_disable_rate_limiting(self):
        """Temporarily disable rate limiting"""
        self.config_manager.config.rate_limiting.enabled = False
        return self

    def temporarily_allow_all_cors(self):
        """Temporarily allow all CORS origins (for testing only)"""
        self.config_manager.config.cors.allow_origins = ["*"]
        return self

    def temporarily_reduce_validation(self):
        """Temporarily reduce input validation strictness"""
        self.config_manager.config.validation.block_sql_keywords = False
        self.config_manager.config.validation.block_script_tags = False
        return self
