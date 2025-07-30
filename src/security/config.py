"""
Security Configuration Management

Centralized security configuration management with environment-based settings,
secure defaults, and runtime configuration updates. Handles encryption keys,
security policies, and service-specific security settings.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from enum import Enum
from pathlib import Path
import secrets
from cryptography.fernet import Fernet
import base64

from pydantic import BaseSettings, Field, validator, SecretStr

logger = logging.getLogger(__name__)


class SecurityLevel(str, Enum):
    """Security level configurations"""

    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class EncryptionConfig(BaseSettings):
    """Encryption configuration"""

    encryption_key: Optional[SecretStr] = None
    key_rotation_days: int = 90
    use_hardware_security_module: bool = False

    class Config:
        env_prefix = "ENCRYPTION_"

    def get_encryption_key(self) -> bytes:
        """Get or generate encryption key"""
        if self.encryption_key:
            return base64.b64decode(self.encryption_key.get_secret_value())

        # Generate new key if none provided
        key = Fernet.generate_key()
        logger.warning(
            "No encryption key provided, generated new key. Store this securely."
        )
        return key


class AuthenticationConfig(BaseSettings):
    """Authentication configuration"""

    jwt_secret_key: SecretStr = Field(
        default_factory=lambda: SecretStr(secrets.token_urlsafe(32))
    )
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60
    jwt_refresh_expiration_days: int = 30

    # Password policy
    password_min_length: int = 8
    password_max_length: int = 128
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_digits: bool = True
    password_require_special_chars: bool = True
    password_max_age_days: int = 90
    password_history_count: int = 5

    # Session management
    session_timeout_minutes: int = 30
    max_concurrent_sessions: int = 5
    session_regenerate_on_auth: bool = True

    # Account lockout
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15

    # Multi-factor authentication
    mfa_enabled: bool = False
    mfa_required_for_admin: bool = True
    totp_issuer: str = "EAI-MCP-Codex"

    class Config:
        env_prefix = "AUTH_"


class RateLimitConfig(BaseSettings):
    """Rate limiting configuration"""

    enabled: bool = True
    strategy: str = "sliding_window"  # sliding_window, token_bucket, fixed_window

    # Global rate limits
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000

    # Endpoint-specific limits
    login_attempts_per_minute: int = 5
    api_calls_per_minute: int = 100
    file_upload_per_hour: int = 50

    # Burst handling
    burst_multiplier: float = 1.5
    burst_duration_seconds: int = 60

    class Config:
        env_prefix = "RATE_LIMIT_"


class CORSConfig(BaseSettings):
    """CORS configuration"""

    enabled: bool = True
    allow_origins: List[str] = ["https://localhost:3000"]
    allow_methods: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_headers: List[str] = ["Content-Type", "Authorization", "X-CSRF-Token"]
    allow_credentials: bool = True
    max_age: int = 86400

    class Config:
        env_prefix = "CORS_"

    @validator("allow_origins")
    def validate_origins(cls, v):
        """Validate CORS origins"""
        for origin in v:
            if origin != "*" and not origin.startswith(("http://", "https://")):
                raise ValueError(f"Invalid origin format: {origin}")
        return v


class CSPConfig(BaseSettings):
    """Content Security Policy configuration"""

    enabled: bool = True
    default_src: List[str] = ["'self'"]
    script_src: List[str] = ["'self'"]
    style_src: List[str] = ["'self'", "'unsafe-inline'"]
    img_src: List[str] = ["'self'", "data:", "https:"]
    connect_src: List[str] = ["'self'"]
    font_src: List[str] = ["'self'"]
    object_src: List[str] = ["'none'"]
    media_src: List[str] = ["'self'"]
    frame_src: List[str] = ["'none'"]
    report_uri: Optional[str] = None

    class Config:
        env_prefix = "CSP_"


class SecurityHeadersConfig(BaseSettings):
    """Security headers configuration"""

    x_frame_options: str = "DENY"
    x_content_type_options: str = "nosniff"
    x_xss_protection: str = "1; mode=block"
    referrer_policy: str = "strict-origin-when-cross-origin"

    # HSTS configuration
    hsts_max_age: int = 31536000  # 1 year
    hsts_include_subdomains: bool = True
    hsts_preload: bool = True

    class Config:
        env_prefix = "SECURITY_HEADERS_"


class AuditConfig(BaseSettings):
    """Audit logging configuration"""

    enabled: bool = True
    log_file: str = "audit.log"
    log_level: str = "INFO"

    # What to audit
    audit_authentication: bool = True
    audit_authorization: bool = True
    audit_data_access: bool = True
    audit_system_changes: bool = True
    audit_security_events: bool = True

    # Storage and rotation
    max_log_size_mb: int = 100
    log_rotation_days: int = 365
    compress_rotated_logs: bool = True

    # SIEM integration
    siem_enabled: bool = False
    siem_endpoint: Optional[str] = None
    siem_api_key: Optional[SecretStr] = None

    class Config:
        env_prefix = "AUDIT_"


class ValidationConfig(BaseSettings):
    """Input validation configuration"""

    enabled: bool = True
    max_string_length: int = 10000
    max_array_length: int = 1000
    max_object_depth: int = 10
    max_file_size_mb: int = 100

    # Content filtering
    block_sql_keywords: bool = True
    block_script_tags: bool = True
    allow_html_tags: List[str] = []

    # Sanitization
    normalize_unicode: bool = True
    strip_dangerous_chars: bool = True
    validate_json_structure: bool = True

    class Config:
        env_prefix = "VALIDATION_"


class SecurityConfig(BaseSettings):
    """Main security configuration"""

    # Environment and security level
    security_level: SecurityLevel = SecurityLevel.PRODUCTION
    debug_mode: bool = False

    # Configuration file paths
    config_dir: str = "/etc/eai-mcp-codex/security"
    secrets_file: str = "secrets.json"

    # Sub-configurations
    encryption: EncryptionConfig = Field(default_factory=EncryptionConfig)
    authentication: AuthenticationConfig = Field(default_factory=AuthenticationConfig)
    rate_limiting: RateLimitConfig = Field(default_factory=RateLimitConfig)
    cors: CORSConfig = Field(default_factory=CORSConfig)
    csp: CSPConfig = Field(default_factory=CSPConfig)
    headers: SecurityHeadersConfig = Field(default_factory=SecurityHeadersConfig)
    audit: AuditConfig = Field(default_factory=AuditConfig)
    validation: ValidationConfig = Field(default_factory=ValidationConfig)

    # Service-specific overrides
    service_overrides: Dict[str, Dict[str, Any]] = {}

    class Config:
        env_prefix = "SECURITY_"
        env_nested_delimiter = "__"

    @validator("security_level")
    def adjust_for_security_level(cls, v, values):
        """Adjust settings based on security level"""
        if v == SecurityLevel.DEVELOPMENT:
            values["debug_mode"] = True
        elif v == SecurityLevel.PRODUCTION:
            values["debug_mode"] = False
        return v

    def get_service_config(self, service_name: str) -> Dict[str, Any]:
        """Get configuration for specific service"""
        base_config = self.dict()
        overrides = self.service_overrides.get(service_name, {})

        # Deep merge overrides
        def deep_merge(base: Dict, override: Dict) -> Dict:
            result = base.copy()
            for key, value in override.items():
                if (
                    key in result
                    and isinstance(result[key], dict)
                    and isinstance(value, dict)
                ):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            return result

        return deep_merge(base_config, overrides)


class SecurityConfigManager:
    """Manages security configuration with encryption and updates"""

    def __init__(self, config: Optional[SecurityConfig] = None):
        self.config = config or SecurityConfig()
        self.cipher_suite = None
        self._initialize_encryption()
        self._load_secrets()

    def _initialize_encryption(self):
        """Initialize encryption for sensitive configuration"""
        try:
            key = self.config.encryption.get_encryption_key()
            self.cipher_suite = Fernet(key)
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            self.cipher_suite = None

    def _load_secrets(self):
        """Load encrypted secrets from file"""
        secrets_path = Path(self.config.config_dir) / self.config.secrets_file

        if not secrets_path.exists():
            logger.info("No secrets file found, using environment variables only")
            return

        try:
            with open(secrets_path, "r") as f:
                encrypted_data = json.load(f)

            if self.cipher_suite:
                # Decrypt secrets
                for key, encrypted_value in encrypted_data.items():
                    if isinstance(encrypted_value, str):
                        try:
                            decrypted = self.cipher_suite.decrypt(
                                encrypted_value.encode()
                            ).decode()
                            os.environ[key] = decrypted
                        except Exception:
                            logger.warning(f"Failed to decrypt secret: {key}")

        except Exception as e:
            logger.error(f"Failed to load secrets: {e}")

    def save_secret(self, key: str, value: str):
        """Save encrypted secret to file"""
        if not self.cipher_suite:
            logger.error("Encryption not available, cannot save secret")
            return False

        secrets_path = Path(self.config.config_dir)
        secrets_path.mkdir(parents=True, exist_ok=True)
        secrets_file = secrets_path / self.config.secrets_file

        # Load existing secrets
        secrets = {}
        if secrets_file.exists():
            try:
                with open(secrets_file, "r") as f:
                    secrets = json.load(f)
            except Exception:
                logger.warning("Could not load existing secrets file")

        # Encrypt and save new secret
        try:
            encrypted_value = self.cipher_suite.encrypt(value.encode()).decode()
            secrets[key] = encrypted_value

            with open(secrets_file, "w") as f:
                json.dump(secrets, f, indent=2)

            # Set in environment for immediate use
            os.environ[key] = value

            logger.info(f"Secret saved: {key}")
            return True

        except Exception as e:
            logger.error(f"Failed to save secret {key}: {e}")
            return False

    def update_config(self, section: str, updates: Dict[str, Any]):
        """Update configuration section"""
        if not hasattr(self.config, section):
            raise ValueError(f"Configuration section '{section}' not found")

        section_config = getattr(self.config, section)

        # Validate updates
        for key, value in updates.items():
            if not hasattr(section_config, key):
                logger.warning(f"Unknown configuration key: {section}.{key}")
                continue

            # Type validation
            expected_type = type(getattr(section_config, key))
            if not isinstance(value, expected_type) and value is not None:
                try:
                    value = expected_type(value)
                except (ValueError, TypeError):
                    logger.error(
                        f"Invalid type for {section}.{key}: expected {expected_type.__name__}"
                    )
                    continue

            setattr(section_config, key, value)
            logger.info(f"Updated {section}.{key} = {value}")

    def get_security_summary(self) -> Dict[str, Any]:
        """Get summary of current security configuration"""
        return {
            "security_level": self.config.security_level,
            "encryption_enabled": self.cipher_suite is not None,
            "authentication": {
                "jwt_expiration_minutes": self.config.authentication.jwt_expiration_minutes,
                "mfa_enabled": self.config.authentication.mfa_enabled,
                "max_login_attempts": self.config.authentication.max_login_attempts,
            },
            "rate_limiting": {
                "enabled": self.config.rate_limiting.enabled,
                "requests_per_minute": self.config.rate_limiting.requests_per_minute,
            },
            "cors": {
                "enabled": self.config.cors.enabled,
                "allow_origins": self.config.cors.allow_origins,
            },
            "audit": {
                "enabled": self.config.audit.enabled,
                "siem_enabled": self.config.audit.siem_enabled,
            },
            "validation": {
                "enabled": self.config.validation.enabled,
                "max_file_size_mb": self.config.validation.max_file_size_mb,
            },
        }

    def validate_configuration(self) -> List[str]:
        """Validate current configuration and return warnings"""
        warnings = []

        # Check security level vs settings
        if self.config.security_level == SecurityLevel.PRODUCTION:
            if self.config.debug_mode:
                warnings.append("DEBUG mode enabled in production")

            if not self.config.authentication.mfa_enabled:
                warnings.append("MFA not enabled in production")

            if "*" in self.config.cors.allow_origins:
                warnings.append("CORS allows all origins in production")

            if not self.config.audit.enabled:
                warnings.append("Audit logging disabled in production")

        # Check encryption
        if not self.cipher_suite:
            warnings.append("Encryption not properly configured")

        # Check JWT secret
        jwt_secret = self.config.authentication.jwt_secret_key.get_secret_value()
        if len(jwt_secret) < 32:
            warnings.append("JWT secret key too short")

        # Check rate limiting
        if not self.config.rate_limiting.enabled:
            warnings.append("Rate limiting disabled")

        return warnings

    def export_config(self, include_secrets: bool = False) -> Dict[str, Any]:
        """Export configuration (optionally with secrets masked)"""
        config_dict = self.config.dict()

        if not include_secrets:
            # Mask sensitive values
            def mask_secrets(obj):
                if isinstance(obj, dict):
                    return {k: mask_secrets(v) for k, v in obj.items()}
                elif isinstance(obj, SecretStr):
                    return "***MASKED***"
                elif isinstance(obj, str) and any(
                    keyword in obj.lower()
                    for keyword in ["password", "secret", "key", "token"]
                ):
                    return "***MASKED***"
                else:
                    return obj

            config_dict = mask_secrets(config_dict)

        return config_dict


# Configuration presets for different environments
class SecurityConfigPresets:
    """Predefined security configuration presets"""

    @staticmethod
    def development() -> SecurityConfig:
        """Development environment preset"""
        config = SecurityConfig(security_level=SecurityLevel.DEVELOPMENT)

        # Relaxed settings for development
        config.authentication.mfa_enabled = False
        config.rate_limiting.requests_per_minute = 1000
        config.cors.allow_origins = ["*"]
        config.csp.script_src = ["'self'", "'unsafe-inline'", "'unsafe-eval'"]
        config.validation.block_sql_keywords = False

        return config

    @staticmethod
    def production() -> SecurityConfig:
        """Production environment preset"""
        config = SecurityConfig(security_level=SecurityLevel.PRODUCTION)

        # Strict settings for production
        config.authentication.mfa_enabled = True
        config.authentication.mfa_required_for_admin = True
        config.rate_limiting.enabled = True
        config.cors.allow_origins = []  # Must be explicitly configured
        config.headers.hsts_max_age = 31536000
        config.audit.enabled = True
        config.validation.enabled = True

        return config

    @staticmethod
    def high_security() -> SecurityConfig:
        """High security preset"""
        config = SecurityConfigPresets.production()

        # Enhanced security settings
        config.authentication.jwt_expiration_minutes = 15
        config.authentication.max_login_attempts = 3
        config.authentication.lockout_duration_minutes = 30
        config.rate_limiting.requests_per_minute = 30
        config.validation.max_string_length = 1000
        config.validation.max_file_size_mb = 10

        return config


# Global security configuration manager
_config_manager: Optional[SecurityConfigManager] = None


def get_security_config() -> SecurityConfigManager:
    """Get global security configuration manager"""
    global _config_manager
    if _config_manager is None:
        _config_manager = SecurityConfigManager()
    return _config_manager


def initialize_security_config(
    config: Optional[SecurityConfig] = None,
) -> SecurityConfigManager:
    """Initialize global security configuration"""
    global _config_manager
    _config_manager = SecurityConfigManager(config)
    return _config_manager


def load_config_from_env(env_prefix: str = "SECURITY_") -> SecurityConfig:
    """Load configuration from environment variables"""
    return SecurityConfig(_env_prefix=env_prefix)
