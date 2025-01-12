"""MCP server client implementation."""
import aiohttp
import structlog
from typing import Dict, Any

logger = structlog.get_logger()

class MCPClient:
    """Client for interacting with MCP servers."""
    
    def __init__(self, server_url: str):
        """Initialize the MCP client.
        
        Args:
            server_url: The URL of the MCP server
        """
        self.server_url = server_url
        self.session = None
    
    async def connect(self):
        """Establish connection to the MCP server."""
        if self.session is None:
            self.session = aiohttp.ClientSession()
            logger.info("Connected to MCP server", server_url=self.server_url)
    
    async def disconnect(self):
        """Close the connection to the MCP server."""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("Disconnected from MCP server", server_url=self.server_url)
    
    async def send_command(self, command: str, payload: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send a command to the MCP server.
        
        Args:
            command: The command to send
            payload: Optional payload data
            
        Returns:
            The server's response
        """
        if not self.session:
            await self.connect()
            
        url = f"{self.server_url}/api/{command}"
        async with self.session.post(url, json=payload) as response:
            response.raise_for_status()
            return await response.json()
