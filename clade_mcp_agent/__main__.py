"""Main entry point for the Claude MCP Agent."""
import asyncio
import logging

from .agent import MCPAgent
from .claude_client import ClaudeClient
from .mcp_client import MCPClient


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Run the MCP agent with Claude integration."""
    # Initialize clients
    claude_client = ClaudeClient(api_key='your-api-key')  # Will be configured via env later
    mcp_client = MCPClient()
    
    # Initialize agent
    agent = MCPAgent(claude_client=claude_client, mcp_client=mcp_client)
    
    try:
        logger.info('Starting MCP agent...')
        await agent.start()
        
        # Keep the agent running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info('Shutting down MCP agent...')
    finally:
        await agent.stop()


if __name__ == '__main__':
    asyncio.run(main())
