import os
from typing import Any, Dict, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class BaseServiceSettings(BaseSettings):
    """Base configuration for all services."""

    service_name: str = ""
    service_port: int = 0
    
    # Common service settings
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    
    # Database settings
    database_url: str = Field(default="sqlite:///data/service.db", description="Database URL")
    
    # Redis settings
    redis_url: str = Field(default="redis://localhost:6379", description="Redis URL")
    
    # Security settings
    auth_enabled: bool = Field(default=True, description="Enable authentication")
    secret_key: str = Field(default="", description="Secret key for JWT tokens")
    
    # Metrics settings
    metrics_enabled: bool = Field(default=True, description="Enable metrics collection")
    metrics_port: int = Field(default=9090, description="Metrics endpoint port")

    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=False, extra="ignore"
    )


def load_config_from_env(prefix: str = "") -> Dict[str, Any]:
    """Load configuration from environment variables with optional prefix."""
    config = {}
    for key, value in os.environ.items():
        if prefix and not key.startswith(prefix):
            continue
        
        config_key = key.replace(prefix, "").lower()
        config[config_key] = value
    
    return config


def get_service_config(service_name: str) -> Dict[str, Any]:
    """Get service-specific configuration."""
    base_config = {
        "service_name": service_name,
        "debug": os.getenv("DEBUG", "false").lower() == "true",
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
    }
    
    # Load service-specific config
    service_prefix = f"{service_name.upper().replace('-', '_')}_"
    service_config = load_config_from_env(service_prefix)
    
    return {**base_config, **service_config}


def validate_required_env_vars(required_vars: list[str]) -> None:
    """Validate that required environment variables are set."""
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")


def get_database_config() -> Dict[str, str]:
    """Get database configuration."""
    return {
        "url": os.getenv("DATABASE_URL", "sqlite:///data/service.db"),
        "pool_size": os.getenv("DB_POOL_SIZE", "10"),
        "max_overflow": os.getenv("DB_MAX_OVERFLOW", "20"),
    }
