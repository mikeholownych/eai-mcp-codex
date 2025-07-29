# Tier 2 Security Implementation

This directory contains the comprehensive Tier 2 security implementation for the EAI-MCP-Codex system. This tier provides advanced security features including rate limiting, input validation, security headers, audit logging, and centralized configuration management.

## Components Overview

### 1. Rate Limiting (`rate_limiting.py`)
- **Redis-backed rate limiting** with multiple strategies (sliding window, token bucket, fixed window)
- **Configurable limits** per endpoint, user, and global levels
- **Automatic IP detection** and user-based identification
- **Burst handling** and graceful degradation

#### Key Features:
```python
# Configure rate limiter
rate_limiter = RateLimiter(redis_client, settings)
allowed, info = await rate_limiter.check_rate_limit(
    identifier="user:123", 
    limit=100, 
    window_seconds=60
)

# Use as middleware
rate_middleware = RateLimitMiddleware(rate_limiter)
```

### 2. Input Validation & Sanitization (`validation.py`)
- **SQL injection prevention** with pattern detection
- **XSS protection** through HTML sanitization
- **Unicode normalization** and character filtering
- **Configurable validation rules** per endpoint
- **Deep object validation** with size limits

#### Key Features:
```python
# Create validation middleware
validation_middleware = ValidationMiddleware(ValidationConfig(
    max_string_length=10000,
    block_sql_keywords=True,
    block_script_tags=True
))

# Custom validation decorator
@validation_required("user_input_schema")
async def create_user(request: UserRequest):
    pass
```

### 3. Security Headers (`headers.py`)
- **Content Security Policy (CSP)** with customizable directives
- **HTTP Strict Transport Security (HSTS)** configuration
- **CSRF protection** with token generation and validation
- **CORS handling** with origin validation
- **Comprehensive security headers** (X-Frame-Options, X-XSS-Protection, etc.)

#### Key Features:
```python
# Configure security headers
headers_config = SecurityHeadersConfig()
headers_middleware = SecurityHeadersMiddleware(headers_config)

# CSRF protection built-in
csrf_token = headers_middleware.csrf_protection.generate_token(session_id)
```

### 4. Audit Logging (`audit_logging.py`)
- **Structured security event logging** with correlation IDs
- **Risk scoring** for security events
- **SIEM integration** support
- **Comprehensive event types** (auth, authz, data access, system changes)
- **Context-aware logging** with user and session tracking

#### Key Features:
```python
# Log security events
audit_logger.log_event(
    AuditEventType.LOGIN_FAILURE,
    "Invalid credentials provided",
    severity=AuditEventSeverity.HIGH,
    user_id="user123",
    details={"ip": "192.168.1.1", "attempts": 3}
)

# Audit decorator
@audit_action(AuditEventType.ADMIN_ACTION, "User modification")
async def modify_user(user_id: str):
    pass
```

### 5. Input Validation Schemas (`schemas.py`)
- **Comprehensive Pydantic schemas** for all API endpoints
- **Security-focused validators** preventing common attacks
- **Type-safe validation** with automatic sanitization
- **Reusable schema components** for consistent validation
- **File upload validation** with extension and size limits

#### Key Features:
```python
# Use predefined schemas
class UserRegistration(BaseSecureModel):
    username: Username  # Automatically validated
    password: constr(regex=PASSWORD_PATTERN)
    email: EmailStr
    
# Schema registry for dynamic validation
schema = get_schema("auth.login")
validated_data = validate_request("auth.login", request_data)
```

### 6. Security Configuration (`config.py`)
- **Environment-based configuration** with secure defaults
- **Encrypted secrets management** using Fernet encryption
- **Service-specific overrides** for fine-grained control
- **Configuration validation** with security warnings
- **Runtime configuration updates** with audit trails

#### Key Features:
```python
# Load configuration
config_manager = SecurityConfigManager()
config = config_manager.config

# Save encrypted secrets
config_manager.save_secret("JWT_SECRET", secret_value)

# Environment presets
prod_config = SecurityConfigPresets.production()
dev_config = SecurityConfigPresets.development()
```

### 7. Middleware Integration (`middleware.py`)
- **Unified security stack** combining all components
- **Easy FastAPI integration** with single setup function
- **Environment-specific configurations** (dev, prod, high-security)
- **Endpoint-specific security** rules and overrides
- **Security status monitoring** and health checks

#### Key Features:
```python
# Easy setup
security_stack = await setup_security_middleware(
    app, 
    environment="production",
    redis_client=redis_client
)

# Endpoint-specific security
@secure_endpoint(rate_limit=10, validation_schema="sensitive_data")
async def sensitive_endpoint():
    pass
```

## Installation and Setup

### Prerequisites
```bash
pip install fastapi redis pydantic structlog bleach cryptography
```

### Basic Setup
```python
from fastapi import FastAPI
from src.security.middleware import setup_security_middleware
from src.common.redis_client import RedisClient

app = FastAPI()
redis_client = RedisClient()

# Initialize security middleware
security_stack = await setup_security_middleware(
    app=app,
    environment="production",  # or "development", "high_security"
    redis_client=redis_client
)
```

### Advanced Configuration
```python
from src.security.config import SecurityConfig, SecurityConfigManager

# Custom configuration
config = SecurityConfig(
    security_level="production",
    authentication=AuthenticationConfig(
        jwt_expiration_minutes=30,
        mfa_enabled=True
    ),
    rate_limiting=RateLimitConfig(
        requests_per_minute=100,
        enabled=True
    )
)

config_manager = SecurityConfigManager(config)
security_stack = SecurityMiddlewareStack(app, redis_client, config_manager=config_manager)
```

## Configuration Examples

### Development Environment
```python
# Relaxed security for development
config = SecurityConfigPresets.development()
# - MFA disabled
# - CORS allows all origins
# - Relaxed validation rules
# - Higher rate limits
```

### Production Environment
```python
# Strict security for production
config = SecurityConfigPresets.production()
# - MFA enabled for admins
# - Strict CORS policy
# - Full input validation
# - Comprehensive audit logging
```

### High Security Environment
```python
# Maximum security for sensitive data
config = SecurityConfigPresets.high_security()
# - Short JWT expiration (15 min)
# - Low rate limits
# - Maximum validation strictness
# - Enhanced audit logging
```

## Environment Variables

### Core Settings
```bash
# Security Level
SECURITY_LEVEL=production
SECURITY_DEBUG_MODE=false

# Encryption
ENCRYPTION_KEY=base64-encoded-key
ENCRYPTION_KEY_ROTATION_DAYS=90

# Authentication
AUTH_JWT_SECRET_KEY=your-secret-key
AUTH_JWT_EXPIRATION_MINUTES=60
AUTH_MFA_ENABLED=true
AUTH_MAX_LOGIN_ATTEMPTS=5

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_STRATEGY=sliding_window

# CORS
CORS_ALLOW_ORIGINS=https://app.example.com,https://admin.example.com
CORS_ALLOW_CREDENTIALS=true

# Audit Logging
AUDIT_ENABLED=true
AUDIT_LOG_FILE=audit.log
AUDIT_SIEM_ENABLED=false
```

## Security Monitoring

### Health Check Endpoint
```python
@app.get("/security/status")
async def security_status():
    return security_stack.get_security_status()
```

### Audit Log Analysis
```python
# View recent security events
audit_events = audit_logger.get_recent_events(hours=24)

# Monitor high-risk events
high_risk_events = audit_logger.get_events_by_risk_score(min_score=8)
```

### Rate Limit Monitoring
```python
# Check rate limit status for user
rate_info = await rate_limiter.get_rate_limit_info("user:123")

# Monitor rate limit violations
violations = rate_limiter.get_recent_violations()
```

## Best Practices

### 1. Configuration Management
- Use environment-specific configurations
- Store secrets encrypted, never in code
- Regularly rotate encryption keys
- Validate configuration on startup

### 2. Rate Limiting
- Set appropriate limits per endpoint type
- Use user-based limits for authenticated endpoints
- Monitor and adjust limits based on usage patterns
- Implement graceful degradation for limit exceeded

### 3. Input Validation
- Validate all user inputs at the API boundary
- Use schema-based validation for consistency
- Sanitize data before processing or storage
- Log validation failures for security monitoring

### 4. Audit Logging
- Log all security-relevant events
- Include correlation IDs for request tracking
- Use structured logging for analysis
- Integrate with SIEM systems for real-time monitoring

### 5. Security Headers
- Configure CSP based on your application needs
- Enable HSTS for production HTTPS sites
- Use CSRF protection for state-changing operations
- Regularly review and update security policies

## Troubleshooting

### Common Issues

#### Rate Limiting Not Working
- Check Redis connection: `await redis_client.ping()`
- Verify rate limiting is enabled in configuration
- Check rate limit middleware is added to app

#### Validation Failures
- Review validation configuration settings
- Check input data against schema requirements
- Verify validation middleware order in stack

#### CSRF Token Issues
- Ensure cookies are properly set
- Check CSRF token extraction in requests
- Verify session management configuration

#### Audit Logs Not Appearing
- Check audit configuration is enabled
- Verify log file permissions and path
- Check structured logging configuration

### Debug Mode
```python
# Enable debug logging
import logging
logging.getLogger("security").setLevel(logging.DEBUG)

# Temporarily disable security features
with SecurityContext(config_manager) as ctx:
    ctx.temporarily_disable_rate_limiting()
    # Run debug operations
```

## Security Considerations

1. **Secrets Management**: Never store secrets in code. Use encrypted storage or external secret management systems.

2. **Rate Limiting**: Configure appropriate limits to balance security and usability. Monitor for abuse patterns.

3. **Input Validation**: Always validate and sanitize inputs. Use allowlists rather than blocklists when possible.

4. **Audit Logging**: Ensure comprehensive logging without exposing sensitive data. Regularly review logs for security events.

5. **Configuration Security**: Regularly review and update security configurations. Use the most restrictive settings appropriate for your environment.

6. **Monitoring**: Implement real-time monitoring and alerting for security events. Regularly review security metrics and logs.

## Integration with Services

Each service can customize security settings:

```python
# Service-specific rate limits
config.service_overrides["model_router"] = {
    "rate_limiting": {"requests_per_minute": 200}
}

# Service-specific validation
config.service_overrides["git_worktree"] = {
    "validation": {"max_file_size_mb": 50}
}
```

This Tier 2 security implementation provides a robust foundation for protecting the EAI-MCP-Codex system against common web application vulnerabilities while maintaining flexibility for different deployment environments.