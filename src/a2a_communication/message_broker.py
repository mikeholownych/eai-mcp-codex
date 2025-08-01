"""A2A Message Broker for handling inter-agent communication."""

import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from src.common.redis_client import get_redis_connection

from .models import A2AMessage, AgentRegistration, AgentStatus


logger = logging.getLogger(__name__)


class A2AMessageBroker:
    """Handles A2A message routing, delivery, and persistence."""

    @classmethod
    async def create(cls):
        self = cls()
        self.redis = await get_redis_connection()
        return self

    def __init__(self):

        self.message_ttl = 3600  # 1 hour default TTL

    async def send_message(self, message: A2AMessage) -> bool:
        """Send a message to an agent or broadcast."""
        try:
            message_data = message.model_dump_json()

            if message.recipient_agent_id:
                # Direct message
                queue_key = f"agent:{message.recipient_agent_id}:messages"
                await self.redis.lpush(queue_key, message_data)
                await self.redis.expire(queue_key, self.message_ttl)
            else:
                # Broadcast message
                await self.redis.publish("agent:broadcast", message_data)

            # Store message history
            history_key = f"conversation:{message.conversation_id}:messages"
            await self.redis.lpush(history_key, message_data)
            await self.redis.expire(history_key, 86400)  # 24 hours

            logger.info(
                f"Message {message.id} sent to {message.recipient_agent_id or 'broadcast'}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to send message {message.id}: {e}")
            return False

    async def get_messages(self, agent_id: str, limit: int = 10) -> List[A2AMessage]:
        """Retrieve messages for an agent."""
        try:
            queue_key = f"agent:{agent_id}:messages"
            raw_messages = await self.redis.lrange(queue_key, 0, limit - 1)

            messages = []
            for raw_msg in raw_messages:
                message_data = json.loads(raw_msg)
                messages.append(A2AMessage(**message_data))

            # Remove retrieved messages
            if raw_messages:
                await self.redis.ltrim(queue_key, len(raw_messages), -1)

            return messages

        except Exception as e:
            logger.error(f"Failed to get messages for {agent_id}: {e}")
            return []

    async def register_agent(self, registration: AgentRegistration) -> bool:
        """Register an agent in the system."""
        try:
            agent_key = f"agent:{registration.agent_id}"
            agent_data = registration.model_dump_json()

            await self.redis.setex(agent_key, 300, agent_data)  # 5 minutes TTL

            # Add to agent list by type
            type_key = f"agents:type:{registration.agent_type}"
            await self.redis.sadd(type_key, registration.agent_id)

            logger.info(f"Agent {registration.agent_id} registered")
            return True

        except Exception as e:
            logger.error(f"Failed to register agent {registration.agent_id}: {e}")
            return False

    async def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent from the system."""
        try:
            agent_key = f"agent:{agent_id}"
            agent_data = await self.redis.get(agent_key)

            if agent_data:
                registration = AgentRegistration(**json.loads(agent_data))
                type_key = f"agents:type:{registration.agent_type}"
                await self.redis.srem(type_key, agent_id)

            await self.redis.delete(agent_key)

            logger.info(f"Agent {agent_id} unregistered")
            return True

        except Exception as e:
            logger.error(f"Failed to unregister agent {agent_id}: {e}")
            return False

    async def get_agents_by_type(self, agent_type: str) -> List[str]:
        """Get all registered agents of a specific type."""
        try:
            type_key = f"agents:type:{agent_type}"
            return [
                agent_id.decode() for agent_id in await self.redis.smembers(type_key)
            ]
        except Exception as e:
            logger.error(f"Failed to get agents by type {agent_type}: {e}")
            return []

    async def get_agent(self, agent_id: str) -> Optional[AgentRegistration]:
        """Get agent registration information."""
        try:
            agent_key = f"agent:{agent_id}"
            agent_data = await self.redis.get(agent_key)

            if agent_data:
                return AgentRegistration(**json.loads(agent_data))
            return None

        except Exception as e:
            logger.error(f"Failed to get agent {agent_id}: {e}")
            return None

    async def update_agent_status(self, agent_id: str, status: AgentStatus) -> bool:
        """Update agent status."""
        try:
            agent = await self.get_agent(agent_id)
            if agent:
                agent.status = status
                agent.last_heartbeat = datetime.utcnow()
                return await self.register_agent(agent)
            return False

        except Exception as e:
            logger.error(f"Failed to update status for agent {agent_id}: {e}")
            return False

    async def get_conversation_history(
        self, conversation_id: UUID, limit: int = 50
    ) -> List[A2AMessage]:
        """Get conversation message history."""
        try:
            history_key = f"conversation:{conversation_id}:messages"
            raw_messages = await self.redis.lrange(history_key, 0, limit - 1)

            messages = []
            for raw_msg in raw_messages:
                message_data = json.loads(raw_msg)
                messages.append(A2AMessage(**message_data))

            return list(reversed(messages))  # Return in chronological order

        except Exception as e:
            logger.error(f"Failed to get conversation history {conversation_id}: {e}")
            return []

    async def cleanup_expired_messages(self) -> int:
        """Clean up expired messages and inactive agents."""
        cleaned = 0
        try:
            # Clean up inactive agents
            pattern = "agent:*"
            for key in await self.redis.scan_iter(match=pattern):
                if key.decode().endswith(":messages"):
                    continue

                agent_data = await self.redis.get(key)
                if agent_data:
                    registration = AgentRegistration(**json.loads(agent_data))
                    if datetime.utcnow() - registration.last_heartbeat > timedelta(
                        minutes=10
                    ):
                        await self.unregister_agent(registration.agent_id)
                        cleaned += 1

            logger.info(f"Cleaned up {cleaned} expired agents")
            return cleaned

        except Exception as e:
            logger.error(f"Failed to cleanup expired messages: {e}")
            return 0
