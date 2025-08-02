"""Common exception classes and error handling utilities."""

from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class ServiceError(Exception):
    """Base exception for service errors."""

    def __init__(
        self, message: str, error_code: str = None, details: Dict[str, Any] = None
    ):
        self.message = message
        self.error_code = error_code or "SERVICE_ERROR"
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(ServiceError):
    """Exception for validation errors."""

    def __init__(self, message: str, field: str = None, details: Dict[str, Any] = None):
        super().__init__(message, "VALIDATION_ERROR", details)
        self.field = field


class AuthenticationError(ServiceError):
    """Exception for authentication errors."""

    def __init__(
        self, message: str = "Authentication failed", details: Dict[str, Any] = None
    ):
        super().__init__(message, "AUTH_ERROR", details)


class AuthorizationError(ServiceError):
    """Exception for authorization errors."""

    def __init__(
        self, message: str = "Insufficient permissions", details: Dict[str, Any] = None
    ):
        super().__init__(message, "AUTHZ_ERROR", details)


class ResourceNotFoundError(ServiceError):
    """Exception for resource not found errors."""

    def __init__(
        self, resource_type: str, resource_id: str, details: Dict[str, Any] = None
    ):
        message = f"{resource_type} with ID '{resource_id}' not found"
        super().__init__(message, "RESOURCE_NOT_FOUND", details)
        self.resource_type = resource_type
        self.resource_id = resource_id


class ResourceConflictError(ServiceError):
    """Exception for resource conflict errors."""

    def __init__(
        self, message: str, resource_type: str = None, details: Dict[str, Any] = None
    ):
        super().__init__(message, "RESOURCE_CONFLICT", details)
        self.resource_type = resource_type


class ExternalServiceError(ServiceError):
    """Exception for external service errors."""

    def __init__(
        self,
        service_name: str,
        message: str,
        status_code: int = None,
        details: Dict[str, Any] = None,
    ):
        super().__init__(
            f"External service '{service_name}' error: {message}",
            "EXTERNAL_SERVICE_ERROR",
            details,
        )
        self.service_name = service_name
        self.status_code = status_code


class ConfigurationError(ServiceError):
    """Exception for configuration errors."""

    def __init__(
        self, message: str, config_key: str = None, details: Dict[str, Any] = None
    ):
        super().__init__(message, "CONFIG_ERROR", details)
        self.config_key = config_key


class BusinessLogicError(ServiceError):
    """Exception for business logic errors."""

    def __init__(
        self, message: str, operation: str = None, details: Dict[str, Any] = None
    ):
        super().__init__(message, "BUSINESS_LOGIC_ERROR", details)
        self.operation = operation


# HTTP Exception converters
def service_error_to_http_exception(error: ServiceError) -> HTTPException:
    """Convert a ServiceError to an HTTPException."""
    status_code_map = {
        "VALIDATION_ERROR": status.HTTP_400_BAD_REQUEST,
        "AUTH_ERROR": status.HTTP_401_UNAUTHORIZED,
        "AUTHZ_ERROR": status.HTTP_403_FORBIDDEN,
        "RESOURCE_NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "RESOURCE_CONFLICT": status.HTTP_409_CONFLICT,
        "EXTERNAL_SERVICE_ERROR": status.HTTP_502_BAD_GATEWAY,
        "CONFIG_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "BUSINESS_LOGIC_ERROR": status.HTTP_422_UNPROCESSABLE_ENTITY,
        "SERVICE_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
    }

    status_code = status_code_map.get(
        error.error_code, status.HTTP_500_INTERNAL_SERVER_ERROR
    )

    detail = {
        "error_code": error.error_code,
        "message": error.message,
        "details": error.details,
    }

    return HTTPException(status_code=status_code, detail=detail)


def handle_common_exceptions(func):
    """Decorator to handle common exceptions and convert them to HTTP exceptions."""

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ServiceError as e:
            raise service_error_to_http_exception(e)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error_code": "INVALID_INPUT", "message": str(e)},
            )
        except KeyError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error_code": "MISSING_FIELD",
                    "message": f"Missing required field: {str(e)}",
                },
            )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error_code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                },
            )

    return wrapper


class ErrorContext:
    """Context manager for error handling with logging."""

    def __init__(self, operation: str, logger=None, reraise: bool = True):
        self.operation = operation
        self.logger = logger
        self.reraise = reraise

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            if self.logger:
                self.logger.error(
                    f"Error in operation '{self.operation}': {str(exc_val)}"
                )

            if self.reraise:
                if isinstance(exc_val, ServiceError):
                    # Already a service error, just re-raise
                    return False
                else:
                    # Convert to service error
                    raise ServiceError(
                        f"Operation '{self.operation}' failed: {str(exc_val)}",
                        "OPERATION_ERROR",
                        {
                            "original_error": str(exc_val),
                            "error_type": exc_type.__name__,
                        },
                    ) from exc_val

        return False


# Utility functions for error formatting
def format_validation_errors(errors: list) -> Dict[str, Any]:
    """Format validation errors for API responses."""
    formatted_errors = []
    for error in errors:
        formatted_errors.append(
            {
                "field": ".".join(str(loc) for loc in error.get("loc", [])),
                "message": error.get("msg", ""),
                "type": error.get("type", ""),
                "input": error.get("input"),
            }
        )

    return {
        "error_code": "VALIDATION_ERROR",
        "message": "Validation failed",
        "errors": formatted_errors,
    }


def create_error_response(
    error_code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    status_code: int = 500,
) -> Dict[str, Any]:
    """Create a standardized error response."""
    response = {
        "error": True,
        "error_code": error_code,
        "message": message,
        "timestamp": None,  # Would be set by middleware
    }

    if details:
        response["details"] = details

    return response


def setup_exception_handlers(app):
    """Setup global exception handlers for FastAPI application."""
    from fastapi import Request
    from fastapi.responses import JSONResponse
    from .logging import get_logger
    
    logger = get_logger("exception_handler")
    
    @app.exception_handler(ServiceError)
    async def service_error_handler(request: Request, exc: ServiceError):
        """Handle custom service errors."""
        logger.error(f"Service error: {exc.message}")
        http_exc = service_error_to_http_exception(exc)
        return JSONResponse(
            status_code=http_exc.status_code,
            content=http_exc.detail
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTP exceptions."""
        logger.error(f"HTTP error {exc.status_code}: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": True, "message": exc.detail}
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle general exceptions."""
        logger.error(f"Unhandled exception: {str(exc)}")
        return JSONResponse(
            status_code=500,
            content=create_error_response(
                "INTERNAL_ERROR",
                "An unexpected error occurred"
            )
        )
    
    logger.info("Exception handlers configured")
    return app
