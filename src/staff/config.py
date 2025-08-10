"""Configuration for the Staff Management service."""

from typing import Optional
from pydantic import Field, AliasChoices
from pydantic_settings import BaseSettings


class StaffSettings(BaseSettings):
    """Staff service configuration."""

    # Service configuration
    service_name: str = "staff-service"
    service_port: int = Field(default=8006, validation_alias=AliasChoices("SERVICE_PORT"))

    # Database configuration
    database_url: Optional[str] = Field(default=None, validation_alias=AliasChoices("DATABASE_URL"))

    # Authentication
    require_auth: bool = Field(default=True, validation_alias=AliasChoices("REQUIRE_AUTH"))
    staff_roles: list[str] = Field(
        default=["admin", "manager", "support"], validation_alias=AliasChoices("ALLOWED_ROLES")
    )

    # Pagination defaults
    default_page_size: int = Field(default=20, validation_alias=AliasChoices("DEFAULT_PAGE_SIZE"))
    max_page_size: int = Field(default=100, validation_alias=AliasChoices("MAX_PAGE_SIZE"))

    # Feature flags
    enable_user_management: bool = Field(
        default=True, validation_alias=AliasChoices("ENABLE_USER_MANAGEMENT")
    )
    enable_ticket_management: bool = Field(
        default=True, validation_alias=AliasChoices("ENABLE_TICKET_MANAGEMENT")
    )
    enable_system_monitoring: bool = Field(
        default=True, validation_alias=AliasChoices("ENABLE_SYSTEM_MONITORING")
    )

    model_config = {
        "env_prefix": "STAFF_",
        "extra": "ignore",
        "case_sensitive": False,
    }


# Global settings instance
settings = StaffSettings()
