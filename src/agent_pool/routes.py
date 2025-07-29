"""Agent Pool API routes."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from src.common.logging import get_logger

from .models import (
    AgentInstance, AgentType, TaskRequest, TaskResult, 
    AgentPoolConfig, WorkloadDistribution
)
from .manager import AgentPoolManager


router = APIRouter()
logger = get_logger("agent_pool")

# Initialize global pool manager
pool_manager = AgentPoolManager()


@router.post("/agents/create")
async def create_agent(agent_type: AgentType, agent_name: str) -> AgentInstance:
    """Create a new agent instance."""
    try:
        agent = await pool_manager.create_agent_instance(agent_type, agent_name)
        return agent
    except Exception as e:
        logger.error(f"Failed to create agent: {e}")
        raise HTTPException(status_code=500, detail="Failed to create agent")


@router.delete("/agents/{instance_id}")
async def remove_agent(instance_id: UUID) -> dict:
    """Remove an agent instance."""
    success = await pool_manager.remove_agent_instance(instance_id)
    if not success:
        raise HTTPException(status_code=404, detail="Agent instance not found")
    
    return {"status": "removed", "instance_id": str(instance_id)}


@router.get("/agents")
async def list_agents(
    agent_type: Optional[AgentType] = None,
    state: Optional[str] = None
) -> List[AgentInstance]:
    """List all agent instances with optional filtering."""
    agents = list(pool_manager.agents.values())
    
    if agent_type:
        agents = [a for a in agents if a.agent_type == agent_type]
    
    if state:
        agents = [a for a in agents if a.state.value == state]
    
    return agents


@router.get("/agents/{instance_id}")
async def get_agent(instance_id: UUID) -> AgentInstance:
    """Get a specific agent instance."""
    agent = pool_manager.agents.get(instance_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent instance not found")
    
    return agent


@router.post("/tasks/submit")
async def submit_task(task: TaskRequest) -> dict:
    """Submit a task to the agent pool."""
    success = await pool_manager.submit_task(task)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to submit task")
    
    return {"status": "submitted", "task_id": str(task.task_id)}


@router.post("/tasks/{task_id}/complete")
async def complete_task(task_id: UUID, result: TaskResult) -> dict:
    """Mark a task as completed."""
    # Ensure task_id matches
    if result.task_id != task_id:
        raise HTTPException(status_code=400, detail="Task ID mismatch")
    
    success = await pool_manager.complete_task(result)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to complete task")
    
    return {"status": "completed", "task_id": str(task_id)}


@router.get("/agents/available/{agent_type}")
async def get_available_agents(
    agent_type: AgentType,
    required_capabilities: Optional[List[str]] = Query(None)
) -> List[AgentInstance]:
    """Get available agents of a specific type."""
    available_agents = []
    
    for agent in pool_manager.agents.values():
        if (agent.agent_type == agent_type and 
            agent.state.value == "idle" and 
            agent.workload < agent.max_concurrent_tasks):
            
            # Check capabilities if specified
            if required_capabilities:
                if all(cap in agent.capabilities for cap in required_capabilities):
                    available_agents.append(agent)
            else:
                available_agents.append(agent)
    
    return available_agents


@router.get("/workload/distribution")
async def get_workload_distribution() -> List[WorkloadDistribution]:
    """Get workload distribution across agent types."""
    return await pool_manager.get_workload_distribution()


@router.post("/scaling/auto-scale")
async def trigger_auto_scaling() -> dict:
    """Manually trigger auto-scaling."""
    scaling_actions = await pool_manager.scale_agent_pool()
    return {
        "scaled_up": scaling_actions["scaled_up"],
        "scaled_down": scaling_actions["scaled_down"],
        "timestamp": datetime.utcnow()
    }


@router.get("/config")
async def get_pool_config() -> AgentPoolConfig:
    """Get current agent pool configuration."""
    return pool_manager.config


@router.put("/config")
async def update_pool_config(config: AgentPoolConfig) -> dict:
    """Update agent pool configuration."""
    pool_manager.config = config
    return {"status": "updated", "timestamp": datetime.utcnow()}


@router.get("/stats")
async def get_pool_stats() -> dict:
    """Get agent pool statistics."""
    try:
        total_agents = len(pool_manager.agents)
        working_agents = len([a for a in pool_manager.agents.values() if a.state.value == "working"])
        idle_agents = len([a for a in pool_manager.agents.values() if a.state.value == "idle"])
        
        # Count pending tasks
        total_pending = sum(len(queue) for queue in pool_manager.task_queue.values())
        
        # Agent type distribution
        type_distribution = {}
        for agent_type in AgentType:
            count = len([a for a in pool_manager.agents.values() if a.agent_type == agent_type])
            type_distribution[agent_type.value] = count
        
        return {
            "total_agents": total_agents,
            "working_agents": working_agents,
            "idle_agents": idle_agents,
            "pending_tasks": total_pending,
            "agent_type_distribution": type_distribution,
            "utilization_rate": working_agents / max(1, total_agents),
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Failed to get pool stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get pool stats")


@router.post("/agents/{instance_id}/heartbeat")
async def agent_heartbeat(instance_id: UUID) -> dict:
    """Receive heartbeat from an agent instance."""
    agent = pool_manager.agents.get(instance_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent instance not found")
    
    agent.last_activity = datetime.utcnow()
    
    # Update in Redis
    agent_key = f"agent_pool:instance:{instance_id}"
    pool_manager.redis.setex(agent_key, 3600, agent.model_dump_json())
    
    return {"status": "heartbeat_received", "timestamp": datetime.utcnow()}


@router.get("/tasks/queue/{priority}")
async def get_task_queue(priority: str) -> List[TaskRequest]:
    """Get tasks in a specific priority queue."""
    if priority not in pool_manager.task_queue:
        raise HTTPException(status_code=404, detail="Priority queue not found")
    
    return pool_manager.task_queue[priority]


@router.post("/maintenance/{instance_id}")
async def set_maintenance_mode(instance_id: UUID, enabled: bool) -> dict:
    """Enable/disable maintenance mode for an agent."""
    agent = pool_manager.agents.get(instance_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent instance not found")
    
    from .models import AgentState
    agent.state = AgentState.MAINTENANCE if enabled else AgentState.IDLE
    
    # Update in Redis
    agent_key = f"agent_pool:instance:{instance_id}"
    pool_manager.redis.setex(agent_key, 3600, agent.model_dump_json())
    
    return {
        "status": "maintenance_mode_updated",
        "instance_id": str(instance_id),
        "maintenance_enabled": enabled
    }