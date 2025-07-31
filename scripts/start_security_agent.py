#!/usr/bin/env python3
"""Start the Security Agent service."""

import os
import sys

sys.path.insert(0, os.getcwd())

import asyncio
import os
import signal
import sys

from src.common.logging import get_logger


logger = get_logger("security_agent_startup")


class SecurityAgentService:
    """Security Agent Service wrapper."""

    def __init__(self):
        self.agent = None
        self.running = False

    async def start(self):
        """Start the security agent."""
        try:
            # Get configuration from environment
            agent_id = os.getenv("AGENT_ID", "security-001")
            agent_name = os.getenv("AGENT_NAME", "Primary-Security")

            logger.info(f"Starting Security Agent: {agent_id} ({agent_name})")

            # Create and start agent
            from src.agents.security_agent import SecurityAgent

            self.agent = SecurityAgent(agent_id=agent_id, name=agent_name)

            # Initialize message broker BEFORE starting agent
            from src.a2a_communication.message_broker import A2AMessageBroker

            self.agent.message_broker = await A2AMessageBroker.create()
            self.running = True

            # Start agent in background
            await self.agent.start()

        except Exception as e:
            logger.error(f"Failed to start Security Agent: {e}")
            sys.exit(1)

    async def stop(self):
        """Stop the security agent."""
        if self.agent and self.running:
            logger.info("Stopping Security Agent...")
            await self.agent.stop()
            self.running = False
            logger.info("Security Agent stopped")


# Global service instance
service = SecurityAgentService()


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logger.info(f"Received signal {signum}, shutting down...")
    asyncio.create_task(service.stop())


async def main():
    """Main service function."""
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Start the agent service
        await service.start()

        # Keep running until shutdown
        while service.running:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Service error: {e}")
    finally:
        await service.stop()


if __name__ == "__main__":
    asyncio.run(main())
