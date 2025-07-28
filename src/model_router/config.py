"""Model Router configuration."""

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from src.common.settings import BaseServiceSettings


class Settings(BaseServiceSettings):
    """Configuration for the model router service."""

    service_name: str = "model-router"
    service_port: int = 8001
    rules_file: str = Field("config/routing_rules.yml")

    model_config = SettingsConfigDict(env_prefix="MODEL_ROUTER_")


settings = Settings()  # type: ignore[call-arg]
