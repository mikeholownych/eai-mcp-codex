"""Workflow Orchestrator configuration."""

from pydantic_settings import SettingsConfigDict

from src.common.settings import BaseServiceSettings


class Settings(BaseServiceSettings):
    """Configuration for the workflow orchestrator service."""

    service_name: str = "workflow-orchestrator"
    service_port: int = 8004

    model_config = SettingsConfigDict(env_prefix="WORKFLOW_ORCHESTRATOR_")


settings = Settings()
