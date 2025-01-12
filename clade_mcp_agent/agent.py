"""Main agent implementation coordinating Claude and MCP servers."""
from typing import List, Dict
from .config import settings
from .claude_client import ClaudeClient
from .mcp_client import MCPClient
from .logging import get_logger

logger = get_logger(__name__)

class CladeAgent:
    """Agent that coordinates between Claude and MCP servers."""
    
    def __init__(self):
        """Initialize the agent."""
        self.claude = ClaudeClient()
        self.mcp_clients: Dict[str, MCPClient] = {
            server: MCPClient(server)
            for server in settings.mcp_servers
        }
    
    async def start(self):
        """Start the agent and connect to all MCP servers."""
        logger.info("Starting Clade Agent")
        for server, client in self.mcp_clients.items():
            try:
                await client.connect()
            except Exception as e:
                logger.error("Failed to connect to MCP server",
                           server=server,
                           error=str(e))
    
    async def stop(self):
        """Stop the agent and disconnect from all MCP servers."""
        logger.info("Stopping Clade Agent")
        for client in self.mcp_clients.values():
            await client.disconnect()
    
    async def process_command(self, command: str, server: str = None) -> List[Dict]:
        """Process a command using Claude and send to MCP servers.
        
        Args:
            command: The command to process
            server: Optional specific server to target, if None sends to all
            
        Returns:
            List of responses from MCP servers
        """
        # Get Claude's interpretation/enhancement of the command
        enhanced_command = await self.claude.get_completion(
            f"Process this MCP server command: {command}"
        )
        
        # Send to specified server or all servers
        responses = []
        targets = ([self.mcp_clients[server]]
                  if server else self.mcp_clients.values())
        
        for client in targets:
            try:
                response = await client.send_command(enhanced_command)
                responses.append({
                    "server": client.server_url,
                    "status": "success",
                    "response": response
                })
            except Exception as e:
                responses.append({
                    "server": client.server_url,
                    "status": "error",
                    "error": str(e)
                })
                logger.error("Failed to process command",
                           server=client.server_url,
                           command=enhanced_command,
                           error=str(e))
        
        return responses
