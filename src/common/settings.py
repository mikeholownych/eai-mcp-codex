from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseServiceSettings(BaseSettings):
    """Base configuration for all services."""

    service_name: str = ""
    service_port: int = 0

    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=False, extra="ignore"
    )
