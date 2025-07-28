"""Git Worktree configuration."""

from pydantic_settings import SettingsConfigDict

from src.common.settings import BaseServiceSettings


class Settings(BaseServiceSettings):
    """Configuration for the git worktree service."""

    service_name: str = "git-worktree"
    service_port: int = 8003

    model_config = SettingsConfigDict(env_prefix="GIT_WORKTREE_")


settings = Settings()
