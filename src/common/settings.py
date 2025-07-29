from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List
import os

class BaseServiceSettings(BaseSettings):
    """Base configuration for all services."""
    service_name: str = ""
    service_port: int = 0

    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=False, extra="ignore"
    )

class ModelRouterSettings(BaseServiceSettings):
    """Model router specific settings."""
    rules_file: str = "config/routing_rules.yml"
    service_name: str = "model-router"
    service_port: int = 8001

class PlanManagementSettings(BaseServiceSettings):
    """Plan management specific settings."""
    database_url: str = "sqlite:///data/plans.db"
    service_name: str = "plan-management"
    service_port: int = 8002

class GitWorktreeSettings(BaseServiceSettings):
    """Git worktree specific settings."""
    worktree_base_path: str = "/tmp/worktrees"
    service_name: str = "git-worktree"
    service_port: int = 8003

class WorkflowOrchestratorSettings(BaseServiceSettings):
    """Workflow orchestrator specific settings."""
    workflow_definitions_path: str = "config/workflows"
    service_name: str = "workflow-orchestrator"
    service_port: int = 8004

class VerificationFeedbackSettings(BaseServiceSettings):
    """Verification feedback specific settings."""
    verification_rules_path: str = "config/verification_rules.yml"
    service_name: str = "verification-feedback"
    service_port: int = 8005

class A2ACommunicationSettings(BaseServiceSettings):
    """A2A communication specific settings."""
    message_broker_url: str = "redis://localhost:6379/0"
    channel_prefix: str = "a2a:"
    service_name: str = "a2a-communication"
    service_port: int = 8010

class AgentPoolSettings(BaseServiceSettings):
    """Agent pool specific settings."""
    max_agents: int = 10
    agent_config_file: str = "config/agents.yml"
    service_name: str = "agent-pool"
    service_port: int = 8011

class CollaborationOrchestratorSettings(BaseServiceSettings):
    """Collaboration orchestrator specific settings."""
    consensus_threshold: float = 0.75
    max_collaboration_time: int = 3600  # seconds
    service_name: str = "collaboration-orchestrator"
    service_port: int = 8012

class DeveloperAgentSettings(BaseServiceSettings):
    """Developer agent specific settings."""
    code_generation_model: str = "claude-3-5-sonnet-20241022"
    code_review_model: str = "claude-3-opus-20240229"
    service_name: str = "developer-agent"
    service_port: int = 8013

class PlannerAgentSettings(BaseServiceSettings):
    """Planner agent specific settings."""
    planning_model: str = "claude-3-opus-20240229"
    task_breakdown_depth: int = 3
    service_name: str = "planner-agent"
    service_port: int = 8014

class SecurityAgentSettings(BaseServiceSettings):
    """Security agent specific settings."""
    vulnerability_scan_tool: str = "semgrep"
    security_model: str = "claude-3-opus-20240229"
    service_name: str = "security-agent"
    service_port: int = 8015

class AgentMonitorSettings(BaseServiceSettings):
    """Agent monitor specific settings."""
    refresh_interval_seconds: int = 5
    service_name: str = "agent-monitor"
    service_port: int = 8016

class GlobalSettings(BaseSettings):
    """Global application settings."""
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"
    jwt_secret: str = "super-secret-jwt-key" # IMPORTANT: Change this in production!
    database_url: str = "sqlite:///data/mcp_global.db" # For global data if any
    redis_url: str = "redis://localhost:6379"
    consul_url: str = "http://localhost:8500"
    anthropic_api_key: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=False, extra="ignore"
    )

# Initialize settings for each service
model_router_settings = ModelRouterSettings(_env_prefix="MODEL_ROUTER_")
plan_management_settings = PlanManagementSettings(_env_prefix="PLAN_MANAGEMENT_")
git_worktree_settings = GitWorktreeSettings(_env_prefix="GIT_WORKTREE_")
workflow_orchestrator_settings = WorkflowOrchestratorSettings(_env_prefix="WORKFLOW_ORCHESTRATOR_")
verification_feedback_settings = VerificationFeedbackSettings(_env_prefix="VERIFICATION_FEEDBACK_")
a2a_communication_settings = A2ACommunicationSettings(_env_prefix="A2A_COMMUNICATION_")
agent_pool_settings = AgentPoolSettings(_env_prefix="AGENT_POOL_")
collaboration_orchestrator_settings = CollaborationOrchestratorSettings(_env_prefix="COLLABORATION_ORCHESTRATOR_")
developer_agent_settings = DeveloperAgentSettings(_env_prefix="DEVELOPER_AGENT_")
planner_agent_settings = PlannerAgentSettings(_env_prefix="PLANNER_AGENT_")
security_agent_settings = SecurityAgentSettings(_env_prefix="SECURITY_AGENT_")
agent_monitor_settings = AgentMonitorSettings(_env_prefix="AGENT_MONITOR_")

global_settings = GlobalSettings()

# Set Anthropic API key globally if available
if global_settings.anthropic_api_key:
    os.environ["ANTHROPIC_API_KEY"] = global_settings.anthropic_api_key

# Example of how to use settings in a service:
# from src.common.settings import model_router_settings
# print(model_router_settings.rules_file)

# You can also access global settings:
# from src.common.settings import global_settings
# print(global_settings.log_level)

# To override settings for testing or specific environments,
# set environment variables like:
# MODEL_ROUTER_SERVICE_PORT=8080 python my_app.py

# For production, use a .env file or proper environment variables.
# Ensure .env is not committed to version control.

def get_service_config(service_name: str = "") -> BaseServiceSettings:
    """Get configuration for a specific service."""
    return BaseServiceSettings(service_name=service_name)

def validate_required_env_vars(required_vars: List[str]) -> bool:
    """Validate that all required environment variables are set."""
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    return True