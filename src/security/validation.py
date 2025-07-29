"""
Request Validation and Sanitization Middleware

Provides comprehensive input validation and sanitization for API requests.
Protects against injection attacks, XSS, and malformed data.
"""

import re
import html
import json
import urllib.parse
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime
import bleach
from pydantic import BaseModel, ValidationError, validator
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


class ValidationConfig(BaseModel):
    """Configuration for validation rules"""
    max_string_length: int = 10000
    max_array_length: int = 1000
    max_object_depth: int = 10
    allowed_html_tags: List[str] = []
    allowed_html_attributes: Dict[str, List[str]] = {}
    block_sql_keywords: bool = True
    block_script_tags: bool = True
    normalize_unicode: bool = True
    validate_json_structure: bool = True


class SecurityViolation(Exception):
    """Raised when a security violation is detected"""
    def __init__(self, message: str, violation_type: str, field: Optional[str] = None):
        self.message = message
        self.violation_type = violation_type
        self.field = field
        super().__init__(message)


class InputSanitizer:
    """Handles sanitization of various input types"""
    
    def __init__(self, config: ValidationConfig):
        self.config = config
        
        # SQL injection patterns
        self.sql_patterns = [
            r"(\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b)",
            r"(--|\#|\/\*|\*\/)",
            r"(\b(or|and)\s+\d+\s*=\s*\d+)",
            r"(\'\s*(or|and)\s+\'\w+\'\s*=\s*\'\w+)",
        ]
        
        # Script injection patterns
        self.script_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"vbscript:",
            r"onload\s*=",
            r"onerror\s*=",
            r"onclick\s*=",
        ]
        
        # Compile regex patterns
        self.sql_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.sql_patterns]
        self.script_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.script_patterns]
    
    def sanitize_string(self, value: str, field_name: str = "unknown") -> str:
        """Sanitize string input"""
        if not isinstance(value, str):
            return value
        
        original_value = value
        
        # Length check
        if len(value) > self.config.max_string_length:
            raise SecurityViolation(
                f"String too long: {len(value)} > {self.config.max_string_length}",
                "length_violation",
                field_name
            )
        
        # Unicode normalization
        if self.config.normalize_unicode:
            import unicodedata
            value = unicodedata.normalize('NFKC', value)
        
        # Check for SQL injection
        if self.config.block_sql_keywords:
            for regex in self.sql_regex:
                if regex.search(value):
                    raise SecurityViolation(
                        "Potential SQL injection detected",
                        "sql_injection",
                        field_name
                    )
        
        # Check for script injection
        if self.config.block_script_tags:
            for regex in self.script_regex:
                if regex.search(value):
                    raise SecurityViolation(
                        "Potential script injection detected",
                        "script_injection",
                        field_name
                    )
        
        # HTML sanitization
        if self.config.allowed_html_tags:
            value = bleach.clean(
                value,
                tags=self.config.allowed_html_tags,
                attributes=self.config.allowed_html_attributes,
                strip=True
            )
        else:
            # HTML escape if no tags allowed
            value = html.escape(value)
        
        # URL decode to prevent double encoding attacks
        try:
            decoded = urllib.parse.unquote(value)
            if decoded != value:
                # Recursively check decoded value
                return self.sanitize_string(decoded, field_name)
        except Exception:
            pass  # Invalid URL encoding, keep original
        
        return value
    
    def sanitize_dict(self, data: Dict[str, Any], path: str = "", depth: int = 0) -> Dict[str, Any]:
        """Recursively sanitize dictionary"""
        if depth > self.config.max_object_depth:
            raise SecurityViolation(
                f"Object nesting too deep: {depth} > {self.config.max_object_depth}",
                "depth_violation",
                path
            )
        
        sanitized = {}
        for key, value in data.items():
            field_path = f"{path}.{key}" if path else key
            
            # Sanitize key
            clean_key = self.sanitize_string(str(key), f"{field_path}(key)")
            
            # Sanitize value
            sanitized[clean_key] = self.sanitize_value(value, field_path, depth + 1)
        
        return sanitized
    
    def sanitize_list(self, data: List[Any], path: str = "", depth: int = 0) -> List[Any]:
        """Sanitize list items"""
        if len(data) > self.config.max_array_length:
            raise SecurityViolation(
                f"Array too long: {len(data)} > {self.config.max_array_length}",
                "length_violation",
                path
            )
        
        return [
            self.sanitize_value(item, f"{path}[{i}]", depth)
            for i, item in enumerate(data)
        ]
    
    def sanitize_value(self, value: Any, path: str = "", depth: int = 0) -> Any:
        """Sanitize any value type"""
        if isinstance(value, str):
            return self.sanitize_string(value, path)
        elif isinstance(value, dict):
            return self.sanitize_dict(value, path, depth)
        elif isinstance(value, list):
            return self.sanitize_list(value, path, depth)
        elif isinstance(value, (int, float, bool, type(None))):
            return value
        else:
            # Convert unknown types to string and sanitize
            return self.sanitize_string(str(value), path)


class ValidationMiddleware:
    """FastAPI middleware for request validation and sanitization"""
    
    def __init__(self, config: Optional[ValidationConfig] = None):
        self.config = config or ValidationConfig()
        self.sanitizer = InputSanitizer(self.config)
        self.validation_rules = {}
    
    def add_validation_rule(
        self,
        path: str,
        method: str,
        validator_func: Callable[[Any], Any]
    ):
        """Add custom validation rule for specific endpoint"""
        key = f"{method.upper()}:{path}"
        self.validation_rules[key] = validator_func
    
    async def __call__(self, request: Request, call_next):
        """Process request through validation pipeline"""
        try:
            # Skip validation for certain paths
            if self._should_skip_validation(request):
                return await call_next(request)
            
            # Validate and sanitize request
            await self._validate_request(request)
            
            response = await call_next(request)
            
            # Optionally validate response
            if hasattr(response, 'body'):
                await self._validate_response(response)
            
            return response
            
        except SecurityViolation as e:
            logger.warning(
                f"Security violation detected: {e.violation_type} - {e.message}",
                extra={
                    "violation_type": e.violation_type,
                    "field": e.field,
                    "path": request.url.path,
                    "method": request.method,
                    "client_ip": self._get_client_ip(request)
                }
            )
            
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": "Validation failed",
                    "message": "Request contains invalid or potentially malicious content",
                    "violation_type": e.violation_type
                }
            )
        
        except ValidationError as e:
            logger.info(f"Validation error: {str(e)}")
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={
                    "error": "Validation error",
                    "details": e.errors()
                }
            )
        
        except Exception as e:
            logger.error(f"Validation middleware error: {str(e)}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": "Internal validation error"}
            )
    
    def _should_skip_validation(self, request: Request) -> bool:
        """Check if validation should be skipped for this request"""
        skip_paths = ["/health", "/metrics", "/docs", "/openapi.json"]
        return request.url.path in skip_paths
    
    async def _validate_request(self, request: Request):
        """Validate and sanitize request data"""
        # Validate headers
        self._validate_headers(request)
        
        # Validate query parameters
        if request.query_params:
            sanitized_params = self.sanitizer.sanitize_dict(dict(request.query_params))
            # Note: We can't modify request.query_params directly in FastAPI
            # This would need to be handled in the endpoint
        
        # Validate body for POST/PUT/PATCH requests
        if request.method in ["POST", "PUT", "PATCH"]:
            await self._validate_body(request)
    
    def _validate_headers(self, request: Request):
        """Validate request headers"""
        dangerous_headers = [
            "x-forwarded-host",
            "x-original-host",
            "x-rewrite-url"
        ]
        
        for header in dangerous_headers:
            if header in request.headers:
                value = request.headers[header]
                try:
                    self.sanitizer.sanitize_string(value, f"header.{header}")
                except SecurityViolation:
                    raise SecurityViolation(
                        f"Malicious content in header: {header}",
                        "header_injection",
                        header
                    )
    
    async def _validate_body(self, request: Request):
        """Validate request body"""
        content_type = request.headers.get("content-type", "")
        
        if "application/json" in content_type:
            try:
                body = await request.body()
                if body:
                    # Parse JSON
                    try:
                        data = json.loads(body)
                    except json.JSONDecodeError:
                        raise SecurityViolation(
                            "Invalid JSON format",
                            "json_parse_error"
                        )
                    
                    # Validate JSON structure depth and content
                    if self.config.validate_json_structure:
                        self.sanitizer.sanitize_value(data, "body")
                    
                    # Apply custom validation rules
                    endpoint_key = f"{request.method}:{request.url.path}"
                    if endpoint_key in self.validation_rules:
                        validator = self.validation_rules[endpoint_key]
                        validator(data)
            
            except UnicodeDecodeError:
                raise SecurityViolation(
                    "Invalid character encoding in request body",
                    "encoding_error"
                )
    
    async def _validate_response(self, response: Response):
        """Validate outgoing response (optional)"""
        # This is mainly for preventing data leakage
        if hasattr(response, 'body') and response.body:
            # Check for potential sensitive data patterns
            body_str = response.body.decode('utf-8', errors='ignore')
            
            # Patterns that might indicate sensitive data leakage
            sensitive_patterns = [
                r'password\s*[:=]\s*["\']?[^"\'\s]+',
                r'api[_-]?key\s*[:=]\s*["\']?[^"\'\s]+',
                r'secret\s*[:=]\s*["\']?[^"\'\s]+',
                r'token\s*[:=]\s*["\']?[^"\'\s]+',
            ]
            
            for pattern in sensitive_patterns:
                if re.search(pattern, body_str, re.IGNORECASE):
                    logger.warning(
                        "Potential sensitive data in response",
                        extra={"pattern": pattern}
                    )
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"


class SchemaValidator:
    """Advanced schema validation for API endpoints"""
    
    def __init__(self):
        self.schemas = {}
    
    def register_schema(self, path: str, method: str, schema: BaseModel):
        """Register validation schema for endpoint"""
        key = f"{method.upper()}:{path}"
        self.schemas[key] = schema
    
    def validate_request(self, request: Request, data: Any) -> Any:
        """Validate request against registered schema"""
        endpoint_key = f"{request.method}:{request.url.path}"
        
        if endpoint_key in self.schemas:
            schema = self.schemas[endpoint_key]
            try:
                return schema(**data) if isinstance(data, dict) else schema(data)
            except ValidationError as e:
                raise ValidationError(f"Schema validation failed: {e}")
        
        return data


def create_validation_middleware(config: Optional[ValidationConfig] = None) -> ValidationMiddleware:
    """Factory function to create validation middleware"""
    return ValidationMiddleware(config)


# Common validation schemas
class CommonValidationSchemas:
    """Reusable validation schemas"""
    
    class UserInput(BaseModel):
        username: str
        email: Optional[str] = None
        
        @validator('username')
        def validate_username(cls, v):
            if not re.match(r'^[a-zA-Z0-9_-]+$', v):
                raise ValueError('Username contains invalid characters')
            return v
    
    class SearchQuery(BaseModel):
        query: str
        limit: Optional[int] = 10
        offset: Optional[int] = 0
        
        @validator('query')
        def validate_query(cls, v):
            if len(v.strip()) == 0:
                raise ValueError('Query cannot be empty')
            return v.strip()
    
    class FileUpload(BaseModel):
        filename: str
        content_type: str
        size: int
        
        @validator('filename')
        def validate_filename(cls, v):
            # Block potentially dangerous file extensions
            dangerous_extensions = ['.exe', '.bat', '.cmd', '.scr', '.js', '.vbs']
            if any(v.lower().endswith(ext) for ext in dangerous_extensions):
                raise ValueError('File type not allowed')
            return v