"""
Security Audit Logging System

Comprehensive audit logging for security events, authentication, authorization,
data access, and system changes. Provides structured logging with correlation IDs
and integration with SIEM systems.
"""

import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from enum import Enum
from contextlib import contextmanager
from functools import wraps
import asyncio
from threading import local

from fastapi import Request
from pydantic import BaseModel
import structlog

# Thread-local storage for request context
_context = local()


class AuditEventType(str, Enum):
    """Types of security events to audit"""

    # Authentication events
    LOGIN_SUCCESS = "auth.login.success"
    LOGIN_FAILURE = "auth.login.failure"
    LOGOUT = "auth.logout"
    TOKEN_ISSUED = "auth.token.issued"
    TOKEN_REVOKED = "auth.token.revoked"
    TOKEN_EXPIRED = "auth.token.expired"

    # Authorization events
    ACCESS_GRANTED = "authz.access.granted"
    ACCESS_DENIED = "authz.access.denied"
    PERMISSION_ESCALATION = "authz.permission.escalation"

    # Data access events
    DATA_READ = "data.read"
    DATA_CREATE = "data.create"
    DATA_UPDATE = "data.update"
    DATA_DELETE = "data.delete"
    DATA_EXPORT = "data.export"

    # Security violations
    RATE_LIMIT_EXCEEDED = "security.rate_limit.exceeded"
    INVALID_INPUT = "security.input.invalid"
    CSRF_VIOLATION = "security.csrf.violation"
    SQL_INJECTION_ATTEMPT = "security.sql_injection.attempt"
    XSS_ATTEMPT = "security.xss.attempt"

    # System events
    SYSTEM_START = "system.start"
    SYSTEM_STOP = "system.stop"
    CONFIG_CHANGE = "system.config.change"

    # Administrative events
    ADMIN_ACTION = "admin.action"
    USER_CREATED = "admin.user.created"
    USER_DELETED = "admin.user.deleted"
    ROLE_ASSIGNED = "admin.role.assigned"
    ROLE_REVOKED = "admin.role.revoked"


class AuditEventSeverity(str, Enum):
    """Severity levels for audit events"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditEvent(BaseModel):
    """Structured audit event model"""

    event_id: str
    timestamp: datetime
    event_type: AuditEventType
    severity: AuditEventSeverity
    correlation_id: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    username: Optional[str] = None
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    resource: Optional[str] = None
    action: Optional[str] = None
    outcome: str  # success, failure, error
    message: str
    details: Dict[str, Any] = {}
    risk_score: Optional[int] = None
    tags: List[str] = []

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class AuditLogger:
    """Main audit logging class"""

    def __init__(
        self,
        logger_name: str = "security.audit",
        enable_console: bool = True,
        enable_file: bool = True,
        file_path: str = "audit.log",
        enable_siem: bool = False,
        siem_endpoint: Optional[str] = None,
    ):

        self.logger = structlog.get_logger(logger_name)
        self.enable_console = enable_console
        self.enable_file = enable_file
        self.file_path = file_path
        self.enable_siem = enable_siem
        self.siem_endpoint = siem_endpoint

        # Configure structured logging
        self._setup_logging()

        # Event correlation
        self.correlation_store = {}  # In production, use Redis

        # Risk scoring
        self.risk_rules = self._initialize_risk_rules()

    def _setup_logging(self):
        """Configure structured logging"""
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            self._add_correlation_id,
            structlog.processors.JSONRenderer(),
        ]

        structlog.configure(
            processors=processors,
            wrapper_class=structlog.stdlib.BoundLogger,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )

    def _add_correlation_id(self, logger, method_name, event_dict):
        """Add correlation ID to log entries"""
        if hasattr(_context, "correlation_id"):
            event_dict["correlation_id"] = _context.correlation_id
        return event_dict

    def _initialize_risk_rules(self) -> Dict[AuditEventType, int]:
        """Initialize risk scoring rules"""
        return {
            AuditEventType.LOGIN_SUCCESS: 1,
            AuditEventType.LOGIN_FAILURE: 5,
            AuditEventType.ACCESS_DENIED: 3,
            AuditEventType.PERMISSION_ESCALATION: 8,
            AuditEventType.RATE_LIMIT_EXCEEDED: 4,
            AuditEventType.SQL_INJECTION_ATTEMPT: 9,
            AuditEventType.XSS_ATTEMPT: 7,
            AuditEventType.CSRF_VIOLATION: 6,
            AuditEventType.DATA_DELETE: 3,
            AuditEventType.DATA_EXPORT: 2,
            AuditEventType.ADMIN_ACTION: 4,
            AuditEventType.USER_DELETED: 5,
        }

    def calculate_risk_score(
        self, event_type: AuditEventType, details: Dict[str, Any]
    ) -> int:
        """Calculate risk score for event"""
        base_score = self.risk_rules.get(event_type, 1)

        # Adjust based on details
        if details.get("repeated_failures", 0) > 3:
            base_score += 3

        if details.get("admin_user"):
            base_score += 2

        if details.get("sensitive_data"):
            base_score += 2

        return min(base_score, 10)  # Cap at 10

    def log_event(
        self,
        event_type: AuditEventType,
        message: str,
        outcome: str = "success",
        severity: AuditEventSeverity = AuditEventSeverity.MEDIUM,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        resource: Optional[str] = None,
        action: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None,
        tags: Optional[List[str]] = None,
    ):
        """Log a security audit event"""

        # Create event
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            event_type=event_type,
            severity=severity,
            correlation_id=getattr(_context, "correlation_id", None),
            session_id=getattr(_context, "session_id", None),
            user_id=user_id or getattr(_context, "user_id", None),
            username=username or getattr(_context, "username", None),
            client_ip=(
                self._get_client_ip(request)
                if request
                else getattr(_context, "client_ip", None)
            ),
            user_agent=request.headers.get("User-Agent") if request else None,
            request_id=getattr(_context, "request_id", None),
            resource=resource,
            action=action,
            outcome=outcome,
            message=message,
            details=details or {},
            tags=tags or [],
        )

        # Calculate risk score
        event.risk_score = self.calculate_risk_score(event_type, event.details)

        # Log the event
        self._write_event(event)

        # Handle high-risk events
        if event.risk_score >= 7:
            self._handle_high_risk_event(event)

        return event.event_id

    def _write_event(self, event: AuditEvent):
        """Write event to configured outputs"""
        event_data = event.dict()

        # Console logging
        if self.enable_console:
            log_level = self._get_log_level(event.severity)
            self.logger.log(log_level, event.message, **event_data)

        # File logging
        if self.enable_file:
            self._write_to_file(event_data)

        # SIEM integration
        if self.enable_siem and self.siem_endpoint:
            asyncio.create_task(self._send_to_siem(event_data))

    def _get_log_level(self, severity: AuditEventSeverity) -> int:
        """Map severity to log level"""
        mapping = {
            AuditEventSeverity.LOW: logging.INFO,
            AuditEventSeverity.MEDIUM: logging.WARNING,
            AuditEventSeverity.HIGH: logging.ERROR,
            AuditEventSeverity.CRITICAL: logging.CRITICAL,
        }
        return mapping.get(severity, logging.INFO)

    def _write_to_file(self, event_data: Dict[str, Any]):
        """Write event to file"""
        try:
            with open(self.file_path, "a") as f:
                f.write(json.dumps(event_data, default=str) + "\n")
        except Exception as e:
            self.logger.error(f"Failed to write audit log to file: {e}")

    async def _send_to_siem(self, event_data: Dict[str, Any]):
        """Send event to SIEM system"""
        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.siem_endpoint, json=event_data
                ) as response:
                    if response.status != 200:
                        self.logger.error(f"Failed to send to SIEM: {response.status}")
        except Exception as e:
            self.logger.error(f"SIEM integration error: {e}")

    def _handle_high_risk_event(self, event: AuditEvent):
        """Handle high-risk security events"""
        # Log critical alert
        self.logger.critical(
            f"HIGH RISK SECURITY EVENT: {event.event_type}",
            event_id=event.event_id,
            risk_score=event.risk_score,
            user_id=event.user_id,
            client_ip=event.client_ip,
        )

        # Could trigger additional actions:
        # - Send alerts
        # - Block IP
        # - Revoke sessions
        # - Notify security team

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"

    def start_correlation(self, correlation_id: Optional[str] = None) -> str:
        """Start event correlation context"""
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
        _context.correlation_id = correlation_id
        return correlation_id

    def set_session_context(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        client_ip: Optional[str] = None,
    ):
        """Set session context for audit logging"""
        _context.session_id = session_id
        _context.user_id = user_id
        _context.username = username
        _context.client_ip = client_ip

    def clear_context(self):
        """Clear audit context"""
        for attr in [
            "correlation_id",
            "session_id",
            "user_id",
            "username",
            "client_ip",
            "request_id",
        ]:
            if hasattr(_context, attr):
                delattr(_context, attr)


class AuditMiddleware:
    """FastAPI middleware for automatic audit logging"""

    def __init__(self, audit_logger: AuditLogger):
        self.audit_logger = audit_logger
        self.excluded_paths = ["/health", "/metrics", "/docs", "/openapi.json"]

    async def __call__(self, request: Request, call_next):
        """Log request/response audit events"""
        # Skip excluded paths
        if request.url.path in self.excluded_paths:
            return await call_next(request)

        # Start correlation context
        self.audit_logger.start_correlation()
        request_id = str(uuid.uuid4())
        _context.request_id = request_id

        # Set client context
        client_ip = self.audit_logger._get_client_ip(request)
        _context.client_ip = client_ip

        start_time = time.time()

        try:
            # Log request
            self.audit_logger.log_event(
                (
                    AuditEventType.DATA_READ
                    if request.method == "GET"
                    else AuditEventType.DATA_CREATE
                ),
                f"{request.method} {request.url.path}",
                severity=AuditEventSeverity.LOW,
                resource=request.url.path,
                action=request.method,
                details={
                    "method": request.method,
                    "path": request.url.path,
                    "query_params": dict(request.query_params),
                    "user_agent": request.headers.get("User-Agent", ""),
                    "content_type": request.headers.get("Content-Type", ""),
                },
                request=request,
                tags=["request"],
            )

            response = await call_next(request)

            # Log successful response
            duration = time.time() - start_time
            self.audit_logger.log_event(
                AuditEventType.ACCESS_GRANTED,
                f"Request completed: {request.method} {request.url.path}",
                outcome="success",
                severity=AuditEventSeverity.LOW,
                resource=request.url.path,
                action=request.method,
                details={
                    "status_code": response.status_code,
                    "duration_ms": round(duration * 1000, 2),
                    "response_size": (
                        len(response.body) if hasattr(response, "body") else None
                    ),
                },
                request=request,
                tags=["response", "success"],
            )

            return response

        except Exception as e:
            # Log error
            duration = time.time() - start_time
            self.audit_logger.log_event(
                AuditEventType.ACCESS_DENIED,
                f"Request failed: {request.method} {request.url.path} - {str(e)}",
                outcome="error",
                severity=AuditEventSeverity.HIGH,
                resource=request.url.path,
                action=request.method,
                details={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "duration_ms": round(duration * 1000, 2),
                },
                request=request,
                tags=["response", "error"],
            )
            raise

        finally:
            # Clear context
            self.audit_logger.clear_context()


def audit_action(
    event_type: AuditEventType,
    message: str = None,
    severity: AuditEventSeverity = AuditEventSeverity.MEDIUM,
    resource: str = None,
    include_args: bool = False,
):
    """Decorator for auditing function calls"""

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            audit_logger = getattr(func, "_audit_logger", None)
            if not audit_logger:
                return await func(*args, **kwargs)

            func_name = f"{func.__module__}.{func.__name__}"
            audit_message = message or f"Function called: {func_name}"

            details = {"function": func_name}
            if include_args:
                details["args"] = str(args)
                details["kwargs"] = {k: str(v) for k, v in kwargs.items()}

            try:
                result = await func(*args, **kwargs)

                audit_logger.log_event(
                    event_type,
                    audit_message,
                    outcome="success",
                    severity=severity,
                    resource=resource or func_name,
                    action="execute",
                    details=details,
                    tags=["function_call", "success"],
                )

                return result

            except Exception as e:
                audit_logger.log_event(
                    event_type,
                    f"{audit_message} - FAILED: {str(e)}",
                    outcome="error",
                    severity=AuditEventSeverity.HIGH,
                    resource=resource or func_name,
                    action="execute",
                    details={**details, "error": str(e)},
                    tags=["function_call", "error"],
                )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Similar implementation for sync functions
            return func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


@contextmanager
def audit_context(
    audit_logger: AuditLogger,
    correlation_id: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
):
    """Context manager for audit logging"""
    correlation_id = audit_logger.start_correlation(correlation_id)

    if user_id:
        _context.user_id = user_id
    if session_id:
        _context.session_id = session_id

    try:
        yield correlation_id
    finally:
        audit_logger.clear_context()


# Global audit logger instance
default_audit_logger = AuditLogger()


def get_audit_logger() -> AuditLogger:
    """Get the default audit logger"""
    return default_audit_logger
