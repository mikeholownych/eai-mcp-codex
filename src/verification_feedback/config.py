"""Verification Feedback configuration."""

from pydantic_settings import SettingsConfigDict

from src.common.settings import BaseServiceSettings


class Settings(BaseServiceSettings):
    """Configuration for the verification feedback service."""

    service_name: str = "verification-feedback"
    service_port: int = 8005
    database_url: str = "postgresql://mcp_user:mcp_password@localhost:5432/verification_feedback_db"

    model_config = SettingsConfigDict(env_prefix="VERIFICATION_FEEDBACK_")


settings = Settings()