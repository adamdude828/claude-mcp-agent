"""Entry point for running the agent."""

import asyncio

import structlog

from .agent import CladeAgent
from .config import settings


# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ]
)

logger = structlog.get_logger()


async def main():
    """Main entry point for the agent.

    Initializes and runs the Clade agent, handling graceful shutdown on interrupt.
    """
    agent = CladeAgent()
    
    try:
        await agent.start()
        # Keep the agent running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    finally:
        await agent.stop()


if __name__ == "__main__":
    asyncio.run(main())
