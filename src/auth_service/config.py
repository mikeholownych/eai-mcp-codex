"""Configuration for Auth Service."""

import os
from pydantic_settings import BaseSettings
from typing import Optional


class AuthConfig(BaseSettings):
    """Authentication service configuration."""
    
    # Service configuration
    service_name: str = "auth-service"
    service_port: int = 8007
    service_host: str = "0.0.0.0"
    
    # Database configuration
    database_url: str = "postgresql://mcp_user:mcp_secure_password@postgres:5432/auth_db"
    
    # Redis configuration
    redis_url: str = "redis://redis:6379"
    
    # Consul configuration
    consul_url: str = "http://consul:8500"
    
    # JWT configuration
    jwt_secret_key: str = "your-super-secret-jwt-key-change-in-production"
    jwt_expiry_hours: int = 24
    jwt_algorithm: str = "HS256"
    
    # OAuth configuration
    github_client_id: Optional[str] = None
    github_client_secret: Optional[str] = None
    enable_github_oauth: bool = False
    
    # Security configuration
    password_min_length: int = 8
    api_key_length: int = 32
    session_timeout_hours: int = 24 * 7  # 7 days
    
    # Rate limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 3600  # 1 hour
    
    # Environment
    environment: str = "development"
    debug: bool = False
    
    class Config:
        env_prefix = ""
        case_sensitive = False


def get_config() -> AuthConfig:
    """Get configuration instance."""
    return AuthConfig()