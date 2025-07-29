"""Agent Pool Manager for managing agent instances and task distribution."""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import UUID

from src.common.redis_client import get_redis_connection

from .models import (
    AgentInstance, AgentState, AgentType, TaskRequest, 
    TaskResult, AgentPoolConfig, WorkloadDistribution
)


logger = logging.getLogger(__name__)


class AgentPoolManager:
    """Manages a pool of agent instances and task distribution."""
    
    def __init__(self, config: AgentPoolConfig = None):
        self.config = config or AgentPoolConfig()
        self.redis = get_redis_connection()
        self.agents: Dict[UUID, AgentInstance] = {}
        self.task_queue: Dict[str, List[TaskRequest]] = {}  # priority -> tasks
        
        # Initialize task queues
        for priority in ["urgent", "high", "medium", "low"]:
            self.task_queue[priority] = []
    
    async def create_agent_instance(self, agent_type: AgentType, agent_name: str) -> AgentInstance:
        """Create a new agent instance."""
        agent = AgentInstance(
            agent_type=agent_type,
            agent_name=agent_name,
            capabilities=self._get_default_capabilities(agent_type),
            configuration=self._get_default_config(agent_type)
        )
        
        self.agents[agent.instance_id] = agent
        
        # Store in Redis
        agent_key = f"agent_pool:instance:{agent.instance_id}"
        self.redis.setex(agent_key, 3600, agent.model_dump_json())
        
        # Add to type index
        type_key = f"agent_pool:type:{agent_type}"
        self.redis.sadd(type_key, str(agent.instance_id))
        
        logger.info(f"Created agent instance {agent.instance_id} of type {agent_type}")
        return agent
    
    async def remove_agent_instance(self, instance_id: UUID) -> bool:
        """Remove an agent instance."""
        if instance_id not in self.agents:
            return False
        
        agent = self.agents[instance_id]
        
        # Remove from Redis
        agent_key = f"agent_pool:instance:{instance_id}"
        self.redis.delete(agent_key)
        
        # Remove from type index
        type_key = f"agent_pool:type:{agent.agent_type}"
        self.redis.srem(type_key, str(instance_id))
        
        # Remove from memory
        del self.agents[instance_id]
        
        logger.info(f"Removed agent instance {instance_id}")
        return True
    
    async def submit_task(self, task: TaskRequest) -> bool:
        """Submit a task to the agent pool."""
        try:
            # Add to appropriate priority queue
            priority_queue = self.task_queue.get(task.priority.value, self.task_queue["medium"])
            priority_queue.append(task)
            
            # Store in Redis
            task_key = f"agent_pool:task:{task.task_id}"
            self.redis.setex(task_key, 7200, task.model_dump_json())  # 2 hours TTL
            
            # Add to priority queue in Redis
            queue_key = f"agent_pool:queue:{task.priority.value}"
            self.redis.lpush(queue_key, str(task.task_id))
            
            logger.info(f"Task {task.task_id} submitted with priority {task.priority}")
            
            # Try to assign immediately
            await self._assign_tasks()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to submit task {task.task_id}: {e}")
            return False
    
    async def get_available_agent(self, agent_type: AgentType, required_capabilities: List[str] = None) -> Optional[AgentInstance]:
        """Find an available agent of the specified type."""
        candidates = [
            agent for agent in self.agents.values()
            if (agent.agent_type == agent_type and 
                agent.state == AgentState.IDLE and 
                agent.workload < agent.max_concurrent_tasks)
        ]
        
        # Filter by capabilities if specified
        if required_capabilities:
            candidates = [
                agent for agent in candidates
                if all(cap in agent.capabilities for cap in required_capabilities)
            ]
        
        # Sort by workload (prefer less busy agents)
        candidates.sort(key=lambda a: a.workload)
        
        return candidates[0] if candidates else None
    
    async def assign_task_to_agent(self, task: TaskRequest, agent: AgentInstance) -> bool:
        """Assign a specific task to a specific agent."""
        try:
            # Update agent state
            agent.state = AgentState.WORKING
            agent.current_task_id = task.task_id
            agent.workload += 1
            agent.last_activity = datetime.utcnow()
            
            # Update in Redis
            agent_key = f"agent_pool:instance:{agent.instance_id}"
            self.redis.setex(agent_key, 3600, agent.model_dump_json())
            
            # Create task assignment record
            assignment_key = f"agent_pool:assignment:{task.task_id}"
            assignment_data = {
                "task_id": str(task.task_id),
                "agent_instance_id": str(agent.instance_id),
                "assigned_at": datetime.utcnow().isoformat(),
                "deadline": task.deadline.isoformat() if task.deadline else None
            }
            self.redis.setex(assignment_key, 7200, json.dumps(assignment_data))
            
            logger.info(f"Assigned task {task.task_id} to agent {agent.instance_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to assign task {task.task_id} to agent {agent.instance_id}: {e}")
            return False
    
    async def complete_task(self, task_result: TaskResult) -> bool:
        """Mark a task as completed and update agent state."""
        try:
            # Find the agent
            agent = self.agents.get(task_result.agent_instance_id)
            if not agent:
                logger.error(f"Agent {task_result.agent_instance_id} not found")
                return False
            
            # Update agent state
            agent.state = AgentState.IDLE
            agent.current_task_id = None
            agent.workload = max(0, agent.workload - 1)
            agent.last_activity = datetime.utcnow()
            
            # Update performance metrics
            if "avg_execution_time" not in agent.performance_metrics:
                agent.performance_metrics["avg_execution_time"] = task_result.execution_time
            else:
                current_avg = agent.performance_metrics["avg_execution_time"]
                agent.performance_metrics["avg_execution_time"] = (current_avg + task_result.execution_time) / 2
            
            agent.performance_metrics["total_tasks"] = agent.performance_metrics.get("total_tasks", 0) + 1
            if task_result.status == "completed":
                agent.performance_metrics["success_rate"] = agent.performance_metrics.get("success_rate", 0) + 1
            
            # Update in Redis
            agent_key = f"agent_pool:instance:{agent.instance_id}"
            self.redis.setex(agent_key, 3600, agent.model_dump_json())
            
            # Store task result
            result_key = f"agent_pool:result:{task_result.task_id}"
            self.redis.setex(result_key, 86400, task_result.model_dump_json())  # 24 hours TTL
            
            # Clean up assignment
            assignment_key = f"agent_pool:assignment:{task_result.task_id}"
            self.redis.delete(assignment_key)
            
            logger.info(f"Task {task_result.task_id} completed by agent {task_result.agent_instance_id}")
            
            # Try to assign more tasks
            await self._assign_tasks()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to complete task {task_result.task_id}: {e}")
            return False
    
    async def get_workload_distribution(self) -> List[WorkloadDistribution]:
        """Get workload distribution across agent types."""
        distributions = []
        
        for agent_type in AgentType:
            agents_of_type = [a for a in self.agents.values() if a.agent_type == agent_type]
            
            total_instances = len(agents_of_type)
            active_instances = len([a for a in agents_of_type if a.state != AgentState.MAINTENANCE])
            idle_instances = len([a for a in agents_of_type if a.state == AgentState.IDLE])
            working_instances = len([a for a in agents_of_type if a.state == AgentState.WORKING])
            
            # Count pending tasks for this agent type
            pending_tasks = sum(
                len([t for t in queue if t.required_agent_type == agent_type])
                for queue in self.task_queue.values()
            )
            
            utilization_rate = working_instances / max(1, active_instances)
            
            # Calculate average response time
            response_times = [
                a.performance_metrics.get("avg_execution_time", 0)
                for a in agents_of_type
                if "avg_execution_time" in a.performance_metrics
            ]
            avg_response_time = sum(response_times) / max(1, len(response_times))
            
            distributions.append(WorkloadDistribution(
                agent_type=agent_type,
                total_instances=total_instances,
                active_instances=active_instances,
                idle_instances=idle_instances,
                working_instances=working_instances,
                pending_tasks=pending_tasks,
                utilization_rate=utilization_rate,
                average_response_time=avg_response_time
            ))
        
        return distributions
    
    async def scale_agent_pool(self) -> Dict[str, int]:
        """Auto-scale the agent pool based on workload."""
        scaling_actions = {"scaled_up": 0, "scaled_down": 0}
        
        if not self.config.auto_scaling_enabled:
            return scaling_actions
        
        distributions = await self.get_workload_distribution()
        
        for dist in distributions:
            # Scale up if utilization is high
            if (dist.utilization_rate > self.config.scale_up_threshold and 
                dist.total_instances < self.config.max_agents_per_type[dist.agent_type]):
                
                await self.create_agent_instance(
                    dist.agent_type, 
                    f"{dist.agent_type.value}-{dist.total_instances + 1}"
                )
                scaling_actions["scaled_up"] += 1
                logger.info(f"Scaled up {dist.agent_type} agent pool")
            
            # Scale down if utilization is low
            elif (dist.utilization_rate < self.config.scale_down_threshold and 
                  dist.idle_instances > self.config.min_idle_agents):
                
                # Find an idle agent to remove
                idle_agents = [
                    a for a in self.agents.values() 
                    if a.agent_type == dist.agent_type and a.state == AgentState.IDLE
                ]
                
                if idle_agents:
                    await self.remove_agent_instance(idle_agents[0].instance_id)
                    scaling_actions["scaled_down"] += 1
                    logger.info(f"Scaled down {dist.agent_type} agent pool")
        
        return scaling_actions
    
    async def _assign_tasks(self) -> int:
        """Assign pending tasks to available agents."""
        assigned_count = 0
        
        # Process tasks by priority
        for priority in ["urgent", "high", "medium", "low"]:
            queue = self.task_queue[priority]
            
            # Copy list to avoid modification during iteration
            tasks_to_process = list(queue)
            
            for task in tasks_to_process:
                agent = await self.get_available_agent(
                    task.required_agent_type,
                    task.required_capabilities
                )
                
                if agent:
                    if await self.assign_task_to_agent(task, agent):
                        queue.remove(task)
                        assigned_count += 1
                    else:
                        logger.error(f"Failed to assign task {task.task_id}")
                else:
                    # No available agents, break to avoid checking more tasks
                    break
        
        return assigned_count
    
    def _get_default_capabilities(self, agent_type: AgentType) -> List[str]:
        """Get default capabilities for an agent type."""
        capabilities_map = {
            AgentType.PLANNER: ["task_breakdown", "estimation", "dependency_analysis"],
            AgentType.ARCHITECT: ["system_design", "pattern_recognition", "scalability"],
            AgentType.DEVELOPER: ["coding", "debugging", "testing", "documentation"],
            AgentType.SECURITY: ["vulnerability_analysis", "security_review", "compliance"],
            AgentType.QA: ["test_design", "quality_assurance", "automation"],
            AgentType.DOMAIN_EXPERT: ["domain_knowledge", "best_practices", "consultation"],
            AgentType.CODE_REVIEWER: ["code_review", "style_analysis", "performance_review"]
        }
        return capabilities_map.get(agent_type, [])
    
    def _get_default_config(self, agent_type: AgentType) -> Dict[str, any]:
        """Get default configuration for an agent type."""
        return {
            "max_concurrent_tasks": 3,
            "timeout": 1800,  # 30 minutes
            "retry_attempts": 2,
            "priority_boost": agent_type in [AgentType.SECURITY, AgentType.ARCHITECT]
        }