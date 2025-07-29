"""
Security Headers Middleware

Implements comprehensive security headers to protect against common web vulnerabilities.
Includes CSRF protection, XSS prevention, clickjacking protection, and more.
"""

import secrets
import uuid
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


class SecurityHeadersConfig:
    """Configuration for security headers"""
    
    def __init__(self):
        # Content Security Policy
        self.csp_default_src = ["'self'"]
        self.csp_script_src = ["'self'", "'unsafe-inline'"]
        self.csp_style_src = ["'self'", "'unsafe-inline'"]
        self.csp_img_src = ["'self'", "data:", "https:"]
        self.csp_connect_src = ["'self'"]
        self.csp_font_src = ["'self'"]
        self.csp_object_src = ["'none'"]
        self.csp_media_src = ["'self'"]
        self.csp_frame_src = ["'none'"]
        self.csp_report_uri = None
        
        # HSTS (HTTP Strict Transport Security)
        self.hsts_max_age = 31536000  # 1 year
        self.hsts_include_subdomains = True
        self.hsts_preload = True
        
        # Other security headers
        self.x_frame_options = "DENY"  # DENY, SAMEORIGIN, or specific origin
        self.x_content_type_options = "nosniff"
        self.x_xss_protection = "1; mode=block"
        self.referrer_policy = "strict-origin-when-cross-origin"
        self.permissions_policy = {
            "geolocation": [],
            "microphone": [],
            "camera": [],
            "payment": [],
            "usb": [],
            "magnetometer": [],
            "gyroscope": [],
            "speaker": []
        }
        
        # CSRF protection
        self.csrf_protection_enabled = True
        self.csrf_token_header = "X-CSRF-Token"
        self.csrf_cookie_name = "csrf_token"
        self.csrf_cookie_secure = True
        self.csrf_cookie_httponly = True
        self.csrf_cookie_samesite = "strict"
        self.csrf_token_ttl = 3600  # 1 hour
        
        # CORS settings
        self.cors_allow_origins = ["https://localhost:3000"]
        self.cors_allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        self.cors_allow_headers = ["Content-Type", "Authorization", "X-CSRF-Token"]
        self.cors_allow_credentials = True
        self.cors_max_age = 86400  # 24 hours


class CSRFProtection:
    """CSRF token generation and validation"""
    
    def __init__(self, config: SecurityHeadersConfig):
        self.config = config
        self.tokens = {}  # In production, use Redis or database
    
    def generate_token(self, session_id: str) -> str:
        """Generate a new CSRF token"""
        token = secrets.token_urlsafe(32)
        self.tokens[session_id] = {
            "token": token,
            "created": datetime.utcnow(),
            "ttl": self.config.csrf_token_ttl
        }
        return token
    
    def validate_token(self, session_id: str, provided_token: str) -> bool:
        """Validate CSRF token"""
        if session_id not in self.tokens:
            return False
        
        stored_data = self.tokens[session_id]
        
        # Check if token has expired
        if datetime.utcnow() - stored_data["created"] > timedelta(seconds=stored_data["ttl"]):
            del self.tokens[session_id]
            return False
        
        # Compare tokens
        return secrets.compare_digest(stored_data["token"], provided_token)
    
    def get_session_id(self, request: Request) -> str:
        """Get or create session ID"""
        session_id = request.cookies.get("session_id")
        if not session_id:
            session_id = str(uuid.uuid4())
        return session_id
    
    def cleanup_expired_tokens(self):
        """Remove expired tokens"""
        now = datetime.utcnow()
        expired_sessions = []
        
        for session_id, data in self.tokens.items():
            if now - data["created"] > timedelta(seconds=data["ttl"]):
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.tokens[session_id]


class SecurityHeadersMiddleware:
    """FastAPI middleware for adding security headers"""
    
    def __init__(self, config: Optional[SecurityHeadersConfig] = None):
        self.config = config or SecurityHeadersConfig()
        self.csrf_protection = CSRFProtection(self.config)
    
    async def __call__(self, request: Request, call_next):
        """Add security headers to response"""
        try:
            # Handle CORS preflight requests
            if request.method == "OPTIONS":
                return self._create_cors_preflight_response()
            
            # CSRF protection for state-changing methods
            if self.config.csrf_protection_enabled and request.method in ["POST", "PUT", "DELETE", "PATCH"]:
                if not await self._validate_csrf(request):
                    return JSONResponse(
                        status_code=403,
                        content={"error": "CSRF token validation failed"}
                    )
            
            response = await call_next(request)
            
            # Add security headers
            self._add_security_headers(response, request)
            
            # Handle CSRF token for GET requests
            if request.method == "GET" and self.config.csrf_protection_enabled:
                self._add_csrf_token(response, request)
            
            return response
            
        except Exception as e:
            logger.error(f"Security headers middleware error: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"error": "Security middleware error"}
            )
    
    def _add_security_headers(self, response: Response, request: Request):
        """Add all security headers to response"""
        # Content Security Policy
        csp_value = self._build_csp_header()
        if csp_value:
            response.headers["Content-Security-Policy"] = csp_value
        
        # HTTP Strict Transport Security (only for HTTPS)
        if request.url.scheme == "https":
            hsts_parts = [f"max-age={self.config.hsts_max_age}"]
            if self.config.hsts_include_subdomains:
                hsts_parts.append("includeSubDomains")
            if self.config.hsts_preload:
                hsts_parts.append("preload")
            response.headers["Strict-Transport-Security"] = "; ".join(hsts_parts)
        
        # X-Frame-Options
        if self.config.x_frame_options:
            response.headers["X-Frame-Options"] = self.config.x_frame_options
        
        # X-Content-Type-Options
        if self.config.x_content_type_options:
            response.headers["X-Content-Type-Options"] = self.config.x_content_type_options
        
        # X-XSS-Protection (deprecated but still useful for older browsers)
        if self.config.x_xss_protection:
            response.headers["X-XSS-Protection"] = self.config.x_xss_protection
        
        # Referrer Policy
        if self.config.referrer_policy:
            response.headers["Referrer-Policy"] = self.config.referrer_policy
        
        # Permissions Policy
        permissions_policy = self._build_permissions_policy()
        if permissions_policy:
            response.headers["Permissions-Policy"] = permissions_policy
        
        # CORS headers
        self._add_cors_headers(response, request)
        
        # Additional security headers
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
    
    def _build_csp_header(self) -> str:
        """Build Content Security Policy header value"""
        directives = []
        
        if self.config.csp_default_src:
            directives.append(f"default-src {' '.join(self.config.csp_default_src)}")
        
        if self.config.csp_script_src:
            directives.append(f"script-src {' '.join(self.config.csp_script_src)}")
        
        if self.config.csp_style_src:
            directives.append(f"style-src {' '.join(self.config.csp_style_src)}")
        
        if self.config.csp_img_src:
            directives.append(f"img-src {' '.join(self.config.csp_img_src)}")
        
        if self.config.csp_connect_src:
            directives.append(f"connect-src {' '.join(self.config.csp_connect_src)}")
        
        if self.config.csp_font_src:
            directives.append(f"font-src {' '.join(self.config.csp_font_src)}")
        
        if self.config.csp_object_src:
            directives.append(f"object-src {' '.join(self.config.csp_object_src)}")
        
        if self.config.csp_media_src:
            directives.append(f"media-src {' '.join(self.config.csp_media_src)}")
        
        if self.config.csp_frame_src:
            directives.append(f"frame-src {' '.join(self.config.csp_frame_src)}")
        
        if self.config.csp_report_uri:
            directives.append(f"report-uri {self.config.csp_report_uri}")
        
        return "; ".join(directives)
    
    def _build_permissions_policy(self) -> str:
        """Build Permissions Policy header value"""
        policies = []
        
        for feature, allowed_origins in self.config.permissions_policy.items():
            if not allowed_origins:
                policies.append(f"{feature}=()")
            else:
                origins = " ".join(f'"{origin}"' for origin in allowed_origins)
                policies.append(f"{feature}=({origins})")
        
        return ", ".join(policies)
    
    def _add_cors_headers(self, response: Response, request: Request):
        """Add CORS headers"""
        origin = request.headers.get("Origin")
        
        # Check if origin is allowed
        if origin and (origin in self.config.cors_allow_origins or "*" in self.config.cors_allow_origins):
            response.headers["Access-Control-Allow-Origin"] = origin
        elif not origin and "*" in self.config.cors_allow_origins:
            response.headers["Access-Control-Allow-Origin"] = "*"
        
        if self.config.cors_allow_credentials:
            response.headers["Access-Control-Allow-Credentials"] = "true"
        
        response.headers["Access-Control-Allow-Methods"] = ", ".join(self.config.cors_allow_methods)
        response.headers["Access-Control-Allow-Headers"] = ", ".join(self.config.cors_allow_headers)
        response.headers["Access-Control-Max-Age"] = str(self.config.cors_max_age)
    
    def _create_cors_preflight_response(self) -> Response:
        """Create response for CORS preflight requests"""
        response = Response(status_code=200)
        response.headers["Access-Control-Allow-Methods"] = ", ".join(self.config.cors_allow_methods)
        response.headers["Access-Control-Allow-Headers"] = ", ".join(self.config.cors_allow_headers)
        response.headers["Access-Control-Max-Age"] = str(self.config.cors_max_age)
        
        if self.config.cors_allow_credentials:
            response.headers["Access-Control-Allow-Credentials"] = "true"
        
        return response
    
    async def _validate_csrf(self, request: Request) -> bool:
        """Validate CSRF token"""
        # Skip CSRF validation for API endpoints with proper authentication
        if request.headers.get("Authorization"):
            return True
        
        # Get session ID
        session_id = self.csrf_protection.get_session_id(request)
        
        # Get CSRF token from header or form data
        csrf_token = request.headers.get(self.config.csrf_token_header)
        
        if not csrf_token:
            # Try to get from form data for non-JSON requests
            if hasattr(request, 'form'):
                form_data = await request.form()
                csrf_token = form_data.get("csrf_token")
        
        if not csrf_token:
            logger.warning(f"CSRF token missing for {request.method} {request.url.path}")
            return False
        
        is_valid = self.csrf_protection.validate_token(session_id, csrf_token)
        
        if not is_valid:
            logger.warning(f"Invalid CSRF token for session {session_id}")
        
        return is_valid
    
    def _add_csrf_token(self, response: Response, request: Request):
        """Add CSRF token to response"""
        session_id = self.csrf_protection.get_session_id(request)
        csrf_token = self.csrf_protection.generate_token(session_id)
        
        # Set session cookie if not exists
        if not request.cookies.get("session_id"):
            response.set_cookie(
                "session_id",
                session_id,
                secure=True,
                httponly=True,
                samesite="strict"
            )
        
        # Set CSRF token cookie
        response.set_cookie(
            self.config.csrf_cookie_name,
            csrf_token,
            secure=self.config.csrf_cookie_secure,
            httponly=self.config.csrf_cookie_httponly,
            samesite=self.config.csrf_cookie_samesite
        )
        
        # Also include in response headers for JavaScript access
        response.headers["X-CSRF-Token"] = csrf_token


class SecurityHeadersBuilder:
    """Builder class for custom security headers configuration"""
    
    def __init__(self):
        self.config = SecurityHeadersConfig()
    
    def with_csp(
        self,
        default_src: List[str] = None,
        script_src: List[str] = None,
        style_src: List[str] = None,
        img_src: List[str] = None
    ) -> "SecurityHeadersBuilder":
        """Configure Content Security Policy"""
        if default_src:
            self.config.csp_default_src = default_src
        if script_src:
            self.config.csp_script_src = script_src
        if style_src:
            self.config.csp_style_src = style_src
        if img_src:
            self.config.csp_img_src = img_src
        return self
    
    def with_hsts(
        self,
        max_age: int = 31536000,
        include_subdomains: bool = True,
        preload: bool = True
    ) -> "SecurityHeadersBuilder":
        """Configure HTTP Strict Transport Security"""
        self.config.hsts_max_age = max_age
        self.config.hsts_include_subdomains = include_subdomains
        self.config.hsts_preload = preload
        return self
    
    def with_frame_options(self, option: str) -> "SecurityHeadersBuilder":
        """Configure X-Frame-Options"""
        self.config.x_frame_options = option
        return self
    
    def with_csrf_protection(
        self,
        enabled: bool = True,
        token_header: str = "X-CSRF-Token",
        cookie_name: str = "csrf_token"
    ) -> "SecurityHeadersBuilder":
        """Configure CSRF protection"""
        self.config.csrf_protection_enabled = enabled
        self.config.csrf_token_header = token_header
        self.config.csrf_cookie_name = cookie_name
        return self
    
    def with_cors(
        self,
        allow_origins: List[str],
        allow_methods: List[str] = None,
        allow_headers: List[str] = None,
        allow_credentials: bool = True
    ) -> "SecurityHeadersBuilder":
        """Configure CORS"""
        self.config.cors_allow_origins = allow_origins
        if allow_methods:
            self.config.cors_allow_methods = allow_methods
        if allow_headers:
            self.config.cors_allow_headers = allow_headers
        self.config.cors_allow_credentials = allow_credentials
        return self
    
    def build(self) -> SecurityHeadersConfig:
        """Build the configuration"""
        return self.config


def create_security_headers_middleware(config: Optional[SecurityHeadersConfig] = None) -> SecurityHeadersMiddleware:
    """Factory function to create security headers middleware"""
    return SecurityHeadersMiddleware(config)


# Predefined configurations for common scenarios
class SecurityHeadersPresets:
    """Predefined security header configurations"""
    
    @staticmethod
    def strict_api() -> SecurityHeadersConfig:
        """Strict configuration for API-only applications"""
        return (SecurityHeadersBuilder()
                .with_csp(
                    default_src=["'none'"],
                    script_src=["'none'"],
                    style_src=["'none'"],
                    img_src=["'none'"]
                )
                .with_frame_options("DENY")
                .with_csrf_protection(enabled=True)
                .with_cors(
                    allow_origins=["https://api.example.com"],
                    allow_methods=["GET", "POST", "PUT", "DELETE"],
                    allow_credentials=True
                )
                .build())
    
    @staticmethod
    def web_application() -> SecurityHeadersConfig:
        """Configuration for web applications with frontend"""
        return (SecurityHeadersBuilder()
                .with_csp(
                    default_src=["'self'"],
                    script_src=["'self'", "'unsafe-inline'"],
                    style_src=["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"],
                    img_src=["'self'", "data:", "https:"]
                )
                .with_frame_options("SAMEORIGIN")
                .with_csrf_protection(enabled=True)
                .with_cors(
                    allow_origins=["https://app.example.com", "https://www.example.com"],
                    allow_credentials=True
                )
                .build())
    
    @staticmethod
    def development() -> SecurityHeadersConfig:
        """Relaxed configuration for development"""
        return (SecurityHeadersBuilder()
                .with_csp(
                    default_src=["'self'", "'unsafe-inline'", "'unsafe-eval'"],
                    script_src=["'self'", "'unsafe-inline'", "'unsafe-eval'"],
                    style_src=["'self'", "'unsafe-inline'"]
                )
                .with_frame_options("SAMEORIGIN")
                .with_csrf_protection(enabled=False)
                .with_cors(
                    allow_origins=["*"],
                    allow_credentials=False
                )
                .build())