"""Plan Management configuration."""

from pydantic_settings import SettingsConfigDict

from src.common.settings import BaseServiceSettings


class Settings(BaseServiceSettings):
    """Configuration for the plan management service."""

    service_name: str = "plan-management"
    service_port: int = 8002
    database_url: str = (
        "postgresql://mcp_user:mcp_password@localhost:5432/plan_management_db"
    )

    model_config = SettingsConfigDict(env_prefix="PLAN_MANAGEMENT_")


settings = Settings()
