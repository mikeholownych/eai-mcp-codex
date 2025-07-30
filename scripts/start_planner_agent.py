import sys
import os
sys.path.insert(0, os.getcwd())

#!/usr/bin/env python3
"""Start the Planner Agent service."""

import asyncio
import os
import signal
import sys

from src.agents.planner_agent import PlannerAgent
from src.common.logging import get_logger


logger = get_logger("planner_agent_startup")


class PlannerAgentService:
    """Planner Agent Service wrapper."""

    def __init__(self):
        self.agent = None
        self.running = False

    async def start(self):
        """Start the planner agent."""
        try:
            # Get configuration from environment
            agent_id = os.getenv("AGENT_ID", "planner-001")
            agent_name = os.getenv("AGENT_NAME", "Primary-Planner")

            logger.info(f"Starting Planner Agent: {agent_id} ({agent_name})")

            # Create and start agent
            self.agent = PlannerAgent(agent_id=agent_id, name=agent_name)
            self.running = True

            # Start agent in background
            await self.agent.start()

        except Exception as e:
            logger.error(f"Failed to start Planner Agent: {e}")
            sys.exit(1)

    async def stop(self):
        """Stop the planner agent."""
        if self.agent and self.running:
            logger.info("Stopping Planner Agent...")
            await self.agent.stop()
            self.running = False
            logger.info("Planner Agent stopped")


# Global service instance
service = PlannerAgentService()


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
