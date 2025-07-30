"""Configuration for the Staff Management service."""

from typing import Optional
from pydantic import Field
from src.common.settings import BaseSettings


class StaffSettings(BaseSettings):
    """Staff service configuration."""
    
    # Service configuration
    service_name: str = "staff-service"
    service_port: int = Field(default=8006, env="STAFF_SERVICE_PORT")
    
    # Database configuration
    database_url: Optional[str] = Field(default=None, env="STAFF_DATABASE_URL")
    
    # Authentication
    require_auth: bool = Field(default=True, env="STAFF_REQUIRE_AUTH")
    staff_roles: list[str] = Field(default=["admin", "manager", "support"], env="STAFF_ALLOWED_ROLES")
    
    # Pagination defaults
    default_page_size: int = Field(default=20, env="STAFF_DEFAULT_PAGE_SIZE")
    max_page_size: int = Field(default=100, env="STAFF_MAX_PAGE_SIZE")
    
    # Feature flags
    enable_user_management: bool = Field(default=True, env="STAFF_ENABLE_USER_MANAGEMENT")
    enable_ticket_management: bool = Field(default=True, env="STAFF_ENABLE_TICKET_MANAGEMENT")
    enable_system_monitoring: bool = Field(default=True, env="STAFF_ENABLE_SYSTEM_MONITORING")
    
    class Config:
        env_prefix = "STAFF_"


# Global settings instance
settings = StaffSettings()