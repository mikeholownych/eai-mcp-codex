"""Middleware for payment API security and rate limiting."""

import time
import hashlib
import logging
from typing import Dict, Optional, Callable
from functools import wraps
from datetime import datetime, timedelta

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple in-memory rate limiter for payment endpoints."""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = {}
    
    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed based on rate limit."""
        now = time.time()
        
        # Clean old requests outside the window
        if key in self.requests:
            self.requests[key] = [
                req_time for req_time in self.requests[key]
                if now - req_time < self.window_seconds
            ]
        else:
            self.requests[key] = []
        
        # Check if under limit
        if len(self.requests[key]) >= self.max_requests:
            return False
        
        # Add current request
        self.requests[key].append(now)
        return True
    
    def get_remaining_requests(self, key: str) -> int:
        """Get remaining requests allowed for the key."""
        now = time.time()
        
        if key in self.requests:
            self.requests[key] = [
                req_time for req_time in self.requests[key]
                if now - req_time < self.window_seconds
            ]
            return max(0, self.max_requests - len(self.requests[key]))
        
        return self.max_requests


class PaymentSecurityMiddleware:
    """Middleware for payment security and validation."""
    
    def __init__(self):
        self.rate_limiter = RateLimiter()
        self.blocked_ips: set = set()
        self.suspicious_activity: Dict[str, int] = {}
    
    async def __call__(self, request: Request, call_next):
        """Process the request through security middleware."""
        client_ip = self._get_client_ip(request)
        
        # Check if IP is blocked
        if client_ip in self.blocked_ips:
            logger.warning(f"Blocked request from blocked IP: {client_ip}")
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"error": "Access denied"}
            )
        
        # Rate limiting
        if not self.rate_limiter.is_allowed(client_ip):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"error": "Rate limit exceeded"}
            )
        
        # Security checks
        if not self._validate_request_security(request):
            self._record_suspicious_activity(client_ip)
            logger.warning(f"Suspicious activity detected from IP: {client_ip}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Invalid request"}
            )
        
        # Process request
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        # Check for forwarded headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def _validate_request_security(self, request: Request) -> bool:
        """Validate request security."""
        # Check for required headers
        required_headers = ["User-Agent", "Accept"]
        for header in required_headers:
            if not request.headers.get(header):
                return False
        
        # Check content type for POST requests
        if request.method == "POST":
            content_type = request.headers.get("Content-Type", "")
            if not content_type.startswith("application/json"):
                return False
        
        # Check request size
        content_length = request.headers.get("Content-Length")
        if content_length and int(content_length) > 1024 * 1024:  # 1MB limit
            return False
        
        return True
    
    def _record_suspicious_activity(self, client_ip: str):
        """Record suspicious activity from an IP."""
        if client_ip not in self.suspicious_activity:
            self.suspicious_activity[client_ip] = 0
        
        self.suspicious_activity[client_ip] += 1
        
        # Block IP after 5 suspicious activities
        if self.suspicious_activity[client_ip] >= 5:
            self.blocked_ips.add(client_ip)
            logger.warning(f"IP {client_ip} blocked due to suspicious activity")


def require_authentication(func: Callable):
    """Decorator to require authentication for payment endpoints."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # This would integrate with your auth system
        # For now, we'll just check for a valid API key
        request = kwargs.get('request') or args[0] if args else None
        
        if not request:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key required"
            )
        
        # Validate API key (implement your validation logic)
        if not _validate_api_key(api_key):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        
        return await func(*args, **kwargs)
    
    return wrapper


def _validate_api_key(api_key: str) -> bool:
    """Validate API key (implement your validation logic)."""
    # This is a placeholder - implement your actual API key validation
    # You might check against a database, validate JWT tokens, etc.
    if not api_key or len(api_key) < 32:
        return False
    
    # Add your validation logic here
    return True


def validate_payment_data(data: Dict) -> bool:
    """Validate payment data structure and content."""
    required_fields = ["amount", "currency", "payment_method"]
    
    for field in required_fields:
        if field not in data:
            return False
    
    # Validate amount
    amount = data.get("amount")
    if not isinstance(amount, int) or amount <= 0:
        return False
    
    # Validate currency
    currency = data.get("currency")
    supported_currencies = ["usd", "eur", "gbp", "cad", "aud", "jpy"]
    if currency.lower() not in supported_currencies:
        return False
    
    # Validate payment method
    payment_method = data.get("payment_method")
    if not isinstance(payment_method, dict):
        return False
    
    return True


def sanitize_payment_data(data: Dict) -> Dict:
    """Sanitize payment data for logging (remove sensitive information)."""
    sanitized = data.copy()
    
    # Remove sensitive fields
    sensitive_fields = [
        "card_number", "cvc", "cvv", "card_cvc", "card_cvv",
        "account_number", "routing_number", "ssn", "sin",
        "password", "secret", "key", "token", "api_key"
    ]
    
    for field in sensitive_fields:
        if field in sanitized:
            sanitized[field] = "[REDACTED]"
    
    # Mask card numbers if present
    if "card_number" in sanitized:
        sanitized["card_number"] = _mask_card_number(sanitized["card_number"])
    
    return sanitized


def _mask_card_number(card_number: str) -> str:
    """Mask a card number for logging."""
    if not card_number or len(card_number) < 4:
        return card_number
    
    # Remove spaces and dashes
    card_number = card_number.replace(" ", "").replace("-", "")
    
    if len(card_number) <= 4:
        return card_number
    
    masked = "*" * (len(card_number) - 4) + card_number[-4:]
    
    # Add spaces every 4 characters
    formatted = ""
    for i in range(0, len(masked), 4):
        formatted += masked[i:i+4] + " "
    
    return formatted.strip()


class IdempotencyMiddleware:
    """Middleware for handling idempotency keys."""
    
    def __init__(self):
        self.processed_keys: Dict[str, Dict] = {}
        self.cleanup_interval = 3600  # 1 hour
        self.last_cleanup = time.time()
    
    async def __call__(self, request: Request, call_next):
        """Process request with idempotency check."""
        if request.method in ["POST", "PUT", "PATCH"]:
            idempotency_key = request.headers.get("Idempotency-Key")
            
            if idempotency_key:
                # Check if we've already processed this key
                if idempotency_key in self.processed_keys:
                    cached_response = self.processed_keys[idempotency_key]
                    
                    # Check if response is still valid (within 24 hours)
                    if time.time() - cached_response["timestamp"] < 86400:
                        logger.info(f"Returning cached response for idempotency key: {idempotency_key}")
                        return JSONResponse(
                            status_code=cached_response["status_code"],
                            content=cached_response["content"],
                            headers=cached_response["headers"]
                        )
                    else:
                        # Remove expired cached response
                        del self.processed_keys[idempotency_key]
                
                # Process request
                response = await call_next(request)
                
                # Cache successful responses
                if 200 <= response.status_code < 300:
                    self.processed_keys[idempotency_key] = {
                        "status_code": response.status_code,
                        "content": response.body.decode() if hasattr(response, 'body') else None,
                        "headers": dict(response.headers),
                        "timestamp": time.time()
                    }
                
                return response
        
        # Clean up old keys periodically
        self._cleanup_old_keys()
        
        return await call_next(request)
    
    def _cleanup_old_keys(self):
        """Clean up old idempotency keys."""
        now = time.time()
        if now - self.last_cleanup > self.cleanup_interval:
            cutoff = now - 86400  # 24 hours
            
            expired_keys = [
                key for key, data in self.processed_keys.items()
                if data["timestamp"] < cutoff
            ]
            
            for key in expired_keys:
                del self.processed_keys[key]
            
            self.last_cleanup = now
            logger.debug(f"Cleaned up {len(expired_keys)} expired idempotency keys")
