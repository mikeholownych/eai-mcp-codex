"""Base Agent implementation following AGENTS.md standards."""

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from dataclasses import dataclass

from pydantic import BaseModel, Field

from src.common.logging import get_logger
from src.a2a_communication.message_broker import A2AMessageBroker
from src.a2a_communication.models import (
    A2AMessage,
    AgentRegistration,
    AgentStatus,
    MessageType,
)


@dataclass
class AgentConfig:
    """Agent configuration."""

    agent_id: str
    agent_type: str
    name: str
    capabilities: List[str]
    max_concurrent_tasks: int = 3
    heartbeat_interval: int = 30
    message_poll_interval: int = 5
    auto_register: bool = True


class TaskInput(BaseModel):
    """Standard task input schema."""

    task_id: UUID = Field(default_factory=uuid4)
    task_type: str
    description: str
    context: Dict[str, Any] = Field(default_factory=dict)
    deadline: Optional[datetime] = None
    priority: str = "medium"
    requesting_agent: Optional[str] = None


class TaskOutput(BaseModel):
    """Standard task output schema."""

    task_id: UUID
    status: str  # "completed", "failed", "partial"
    result: Dict[str, Any]
    error_message: Optional[str] = None
    execution_time: float
    agent_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metrics: Dict[str, Any] = Field(default_factory=dict)


class BaseAgent(ABC):
    """Base class for all specialized agents following AGENTS.md standards."""

    @classmethod
    def create(cls, *args, **kwargs):
        """Instantiate an agent with flexible parameters.

        Legacy startup scripts sometimes construct agents by calling
        ``Class.create(agent_id="abc", name="Foo")`` instead of using the
        constructor directly.  This wrapper simply forwards all provided
        arguments to ``__init__`` so those scripts continue to work.
        """

        return cls(*args, **kwargs)

    def __init__(self, config: AgentConfig):
        self.config = config
        self.logger = get_logger(f"agent.{config.agent_type}.{config.agent_id}")

        self.running = False
        self.current_tasks: Dict[UUID, TaskInput] = {}
        self.task_queue: List[TaskInput] = []
        self.last_heartbeat = datetime.utcnow()

        # Performance metrics
        self.metrics = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "total_execution_time": 0.0,
            "average_execution_time": 0.0,
            "uptime_start": datetime.utcnow(),
        }

    @classmethod
    async def create(cls, config: AgentConfig):
        instance = cls(config)
        instance.message_broker = await A2AMessageBroker.create()
        return instance

    async def start(self) -> None:
        """Start the agent."""
        self.running = True
        self.logger.info(f"Starting agent {self.config.agent_id}")

        if self.config.auto_register:
            await self.register()

        # Start background tasks
        await asyncio.gather(
            self._message_loop(),
            self._task_processor(),
            self._heartbeat_loop(),
            self._initialize_agent(),
        )

    async def stop(self) -> None:
        """Stop the agent."""
        self.running = False
        await self.unregister()
        self.logger.info(f"Stopped agent {self.config.agent_id}")

    async def register(self) -> bool:
        """Register agent with the A2A communication system."""
        try:
            registration = AgentRegistration(
                agent_id=self.config.agent_id,
                agent_type=self.config.agent_type,
                capabilities=self.config.capabilities,
                status=AgentStatus.AVAILABLE,
                endpoint=f"agent://{self.config.agent_id}",
                metadata={
                    "name": self.config.name,
                    "max_concurrent_tasks": self.config.max_concurrent_tasks,
                    "started_at": datetime.utcnow().isoformat(),
                },
            )

            success = await self.message_broker.register_agent(registration)
            if success:
                self.logger.info(
                    f"Agent {self.config.agent_id} registered successfully"
                )
            return success

        except Exception as e:
            self.logger.error(f"Failed to register agent: {e}")
            return False

    async def unregister(self) -> bool:
        """Unregister agent from the A2A communication system."""
        try:
            success = await self.message_broker.unregister_agent(self.config.agent_id)
            if success:
                self.logger.info(
                    f"Agent {self.config.agent_id} unregistered successfully"
                )
            return success

        except Exception as e:
            self.logger.error(f"Failed to unregister agent: {e}")
            return False

    async def send_heartbeat(self) -> bool:
        """Send heartbeat to maintain registration."""
        try:
            success = await self.message_broker.update_agent_status(
                self.config.agent_id, AgentStatus.AVAILABLE
            )
            if success:
                self.last_heartbeat = datetime.utcnow()
            return success

        except Exception as e:
            self.logger.error(f"Failed to send heartbeat: {e}")
            return False

    async def submit_task(self, task: TaskInput) -> bool:
        """Submit a task for processing."""
        if len(self.current_tasks) >= self.config.max_concurrent_tasks:
            self.task_queue.append(task)
            self.logger.info(f"Task {task.task_id} queued (at capacity)")
            return True

        self.current_tasks[task.task_id] = task
        self.logger.info(f"Task {task.task_id} accepted for processing")
        return True

    async def _message_loop(self) -> None:
        """Main message processing loop."""
        while self.running:
            try:
                messages = await self.message_broker.get_messages(
                    self.config.agent_id, limit=10
                )

                for message in messages:
                    await self._handle_message(message)

                await asyncio.sleep(self.config.message_poll_interval)

            except Exception as e:
                self.logger.error(f"Error in message loop: {e}")
                await asyncio.sleep(5)  # Back off on error

    async def _task_processor(self) -> None:
        """Process queued and current tasks."""
        while self.running:
            try:
                # Process current tasks
                completed_tasks = []
                for task_id, task in self.current_tasks.items():
                    if await self._is_task_ready(task):
                        result = await self._execute_task(task)
                        await self._complete_task(task, result)
                        completed_tasks.append(task_id)

                # Remove completed tasks
                for task_id in completed_tasks:
                    del self.current_tasks[task_id]

                # Start queued tasks if capacity available
                while (
                    len(self.current_tasks) < self.config.max_concurrent_tasks
                    and self.task_queue
                ):
                    task = self.task_queue.pop(0)
                    self.current_tasks[task.task_id] = task
                    self.logger.info(f"Started queued task {task.task_id}")

                await asyncio.sleep(1)  # Check every second

            except Exception as e:
                self.logger.error(f"Error in task processor: {e}")
                await asyncio.sleep(5)

    async def _heartbeat_loop(self) -> None:
        """Send periodic heartbeats."""
        while self.running:
            try:
                await self.send_heartbeat()
                await asyncio.sleep(self.config.heartbeat_interval)

            except Exception as e:
                self.logger.error(f"Error in heartbeat loop: {e}")
                await asyncio.sleep(10)

    async def _handle_message(self, message: A2AMessage) -> None:
        """Handle incoming A2A messages."""
        try:
            if message.message_type == MessageType.REQUEST:
                await self._handle_task_request(message)
            elif message.message_type == MessageType.COLLABORATION:
                await self._handle_collaboration_request(message)
            elif message.message_type == MessageType.CONSENSUS:
                await self._handle_consensus_request(message)
            elif message.message_type == MessageType.NOTIFICATION:
                await self._handle_notification(message)
            else:
                self.logger.warning(f"Unhandled message type: {message.message_type}")

        except Exception as e:
            self.logger.error(f"Error handling message {message.id}: {e}")

    async def _handle_task_request(self, message: A2AMessage) -> None:
        """Handle task request messages."""
        try:
            payload = message.payload
            task = TaskInput(
                task_id=UUID(payload.get("task_id", str(uuid4()))),
                task_type=payload["task_type"],
                description=payload["description"],
                context=payload.get("context", {}),
                deadline=(
                    datetime.fromisoformat(payload["deadline"])
                    if payload.get("deadline")
                    else None
                ),
                priority=payload.get("priority", "medium"),
                requesting_agent=message.sender_agent_id,
            )

            accepted = await self.submit_task(task)

            # Send response if required
            if message.requires_response:
                response = A2AMessage(
                    sender_agent_id=self.config.agent_id,
                    recipient_agent_id=message.sender_agent_id,
                    message_type=MessageType.RESPONSE,
                    payload={
                        "request_id": str(message.id),
                        "task_id": str(task.task_id),
                        "accepted": accepted,
                        "estimated_completion": (
                            datetime.utcnow() + timedelta(minutes=30)
                        ).isoformat(),
                    },
                    conversation_id=message.conversation_id,
                )
                await self.message_broker.send_message(response)

        except Exception as e:
            self.logger.error(f"Error handling task request: {e}")

    async def _handle_collaboration_request(self, message: A2AMessage) -> None:
        """Handle collaboration invitation messages."""
        try:
            payload = message.payload

            # Check if we can participate
            can_participate = await self._can_participate_in_collaboration(payload)

            # Send response
            response = A2AMessage(
                sender_agent_id=self.config.agent_id,
                recipient_agent_id=message.sender_agent_id,
                message_type=MessageType.RESPONSE,
                payload={
                    "invitation_id": payload.get("invitation_id"),
                    "accepted": can_participate,
                    "capabilities": self.config.capabilities,
                    "message": (
                        "Available for collaboration"
                        if can_participate
                        else "Currently at capacity"
                    ),
                },
                conversation_id=message.conversation_id,
            )
            await self.message_broker.send_message(response)

        except Exception as e:
            self.logger.error(f"Error handling collaboration request: {e}")

    async def _handle_consensus_request(self, message: A2AMessage) -> None:
        """Handle consensus voting requests."""
        try:
            payload = message.payload

            # Make decision based on agent's expertise
            vote = await self._make_consensus_decision(payload)

            # Send vote response
            response = A2AMessage(
                sender_agent_id=self.config.agent_id,
                recipient_agent_id=message.sender_agent_id,
                message_type=MessageType.RESPONSE,
                payload={
                    "decision_id": payload.get("decision_id"),
                    "vote": vote,
                    "reasoning": await self._get_vote_reasoning(payload, vote),
                },
                conversation_id=message.conversation_id,
            )
            await self.message_broker.send_message(response)

        except Exception as e:
            self.logger.error(f"Error handling consensus request: {e}")

    async def _handle_notification(self, message: A2AMessage) -> None:
        """Handle notification messages."""
        self.logger.info(
            f"Notification: {message.payload.get('message', 'No message')}"
        )

    async def _is_task_ready(self, task: TaskInput) -> bool:
        """Check if a task is ready for execution."""
        # Check if deadline has passed
        if task.deadline and datetime.utcnow() > task.deadline:
            self.logger.warning(f"Task {task.task_id} deadline passed")
            return False

        return True

    async def _execute_task(self, task: TaskInput) -> TaskOutput:
        """Execute a task and return result."""
        start_time = datetime.utcnow()

        try:
            # Delegate to agent-specific implementation
            result = await self.process_task(task)

            execution_time = (datetime.utcnow() - start_time).total_seconds()

            # Update metrics
            self.metrics["tasks_completed"] += 1
            self.metrics["total_execution_time"] += execution_time
            self.metrics["average_execution_time"] = (
                self.metrics["total_execution_time"] / self.metrics["tasks_completed"]
            )

            return TaskOutput(
                task_id=task.task_id,
                status="completed",
                result=result,
                execution_time=execution_time,
                agent_id=self.config.agent_id,
                metrics={"processing_time": execution_time},
            )

        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            self.metrics["tasks_failed"] += 1

            self.logger.error(f"Task {task.task_id} failed: {e}")

            return TaskOutput(
                task_id=task.task_id,
                status="failed",
                result={},
                error_message=str(e),
                execution_time=execution_time,
                agent_id=self.config.agent_id,
            )

    async def _complete_task(self, task: TaskInput, result: TaskOutput) -> None:
        """Complete a task and notify requestor if needed."""
        self.logger.info(f"Task {task.task_id} completed with status: {result.status}")

        # Send result to requesting agent if specified
        if task.requesting_agent:
            result_message = A2AMessage(
                sender_agent_id=self.config.agent_id,
                recipient_agent_id=task.requesting_agent,
                message_type=MessageType.RESPONSE,
                payload={
                    "task_result": result.model_dump(),
                    "task_id": str(task.task_id),
                },
            )
            await self.message_broker.send_message(result_message)

    async def _can_participate_in_collaboration(self, payload: Dict[str, Any]) -> bool:
        """Determine if agent can participate in collaboration."""
        required_capabilities = payload.get("capabilities_required", [])

        # Check if we have required capabilities
        has_capabilities = all(
            cap in self.config.capabilities for cap in required_capabilities
        )

        # Check current workload
        at_capacity = len(self.current_tasks) >= self.config.max_concurrent_tasks

        return has_capabilities and not at_capacity

    async def _make_consensus_decision(self, payload: Dict[str, Any]) -> str:
        """Make a consensus decision based on agent's expertise."""
        # Default implementation - can be overridden by specialized agents
        options = payload.get("options", [])
        if options:
            return options[0]  # Default to first option
        return "approve"

    async def _get_vote_reasoning(self, payload: Dict[str, Any], vote: str) -> str:
        """Provide reasoning for a consensus vote."""
        return f"Agent {self.config.agent_id} voted {vote} based on {self.config.agent_type} expertise"

    # Abstract methods that must be implemented by specialized agents

    @abstractmethod
    async def _initialize_agent(self) -> None:
        """Initialize agent-specific resources."""
        pass

    @abstractmethod
    async def process_task(self, task: TaskInput) -> Dict[str, Any]:
        """Process a task and return results."""
        pass

    @abstractmethod
    async def get_capabilities(self) -> List[str]:
        """Get agent's current capabilities."""
        pass

    # Utility methods

    def get_metrics(self) -> Dict[str, Any]:
        """Get agent performance metrics."""
        uptime = (datetime.utcnow() - self.metrics["uptime_start"]).total_seconds()

        return {
            **self.metrics,
            "uptime_seconds": uptime,
            "current_tasks": len(self.current_tasks),
            "queued_tasks": len(self.task_queue),
            "utilization": len(self.current_tasks) / self.config.max_concurrent_tasks,
        }

    def get_status(self) -> Dict[str, Any]:
        """Get agent status information."""
        return {
            "agent_id": self.config.agent_id,
            "agent_type": self.config.agent_type,
            "name": self.config.name,
            "running": self.running,
            "capabilities": self.config.capabilities,
            "current_tasks": len(self.current_tasks),
            "queued_tasks": len(self.task_queue),
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "metrics": self.get_metrics(),
        }
