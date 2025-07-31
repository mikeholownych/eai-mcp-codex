"""Verification Feedback configuration."""

from pydantic_settings import SettingsConfigDict
from pydantic import Field

from src.common.settings import BaseServiceSettings


class Settings(BaseServiceSettings):
    """Configuration for the verification feedback service."""

    service_name: str = "verification-feedback"
    service_port: int = 8005
    database_url: str = Field(
        "postgresql://mcp_user:NoqfMMAgz2TEP0Lcxf6TWWEdIXJqF9o9b4bExZh8@postgres:5432/verification_feedback_db",
        env="VERIFICATION_FEEDBACK_DATABASE_URL",
    )

    model_config = SettingsConfigDict(env_prefix="VERIFICATION_FEEDBACK_")


settings = Settings()
