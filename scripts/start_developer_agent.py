#!/usr/bin/env python3
"""Start the Developer Agent service."""

import asyncio
import os
import signal
import sys
from contextlib import asynccontextmanager

from src.agents.developer_agent import DeveloperAgent
from src.common.logging import get_logger


logger = get_logger("developer_agent_startup")


class DeveloperAgentService:
    """Developer Agent Service wrapper."""
    
    def __init__(self):
        self.agent = None
        self.running = False
    
    async def start(self):
        """Start the developer agent."""
        try:
            # Get configuration from environment
            agent_id = os.getenv("AGENT_ID", "developer-001")
            agent_name = os.getenv("AGENT_NAME", "Primary-Developer")
            specializations_str = os.getenv("SPECIALIZATIONS", "python,javascript,fastapi")
            specializations = [s.strip() for s in specializations_str.split(",")]
            
            logger.info(f"Starting Developer Agent: {agent_id} ({agent_name})")
            logger.info(f"Specializations: {specializations}")
            
            # Create and start agent
            self.agent = DeveloperAgent(
                agent_id=agent_id, 
                name=agent_name,
                specializations=specializations
            )
            self.running = True
            
            # Start agent in background
            await self.agent.start()
            
        except Exception as e:
            logger.error(f"Failed to start Developer Agent: {e}")
            sys.exit(1)
    
    async def stop(self):
        """Stop the developer agent."""
        if self.agent and self.running:
            logger.info("Stopping Developer Agent...")
            await self.agent.stop()
            self.running = False
            logger.info("Developer Agent stopped")


# Global service instance
service = DeveloperAgentService()


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