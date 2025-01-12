"""MCP server client implementation."""
from typing import Optional, Dict, Any
from contextlib import AsyncExitStack
import structlog
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = structlog.get_logger()

class MCPClient:
    """Client for interacting with MCP servers following the Model Context Protocol."""
    
    def __init__(self):
        """Initialize the MCP client."""
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.stdio = None
        self.write = None
    
    async def connect_to_server(self, server_script_path: str, env: Optional[Dict[str, str]] = None):
        """Connect to an MCP server.
        
        Args:
            server_script_path: Path to the server script (.py)
            env: Optional environment variables for the server
        """
        if not server_script_path.endswith('.py'):
            raise ValueError("Server script must be a .py file")
            
        server_params = StdioServerParameters(
            command="python",
            args=[server_script_path],
            env=env
        )
        
        # Setup stdio transport
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        
        # Initialize session
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
        await self.session.initialize()
        
        # List available capabilities
        tools = await self.session.list_tools()
        resources = await self.session.list_resources()
        prompts = await self.session.list_prompts()
        
        logger.info("Connected to MCP server",
                   tools=[tool.name for tool in tools.tools],
                   resources=[r.name for r in resources.resources],
                   prompts=[p.name for p in prompts.prompts])
    
    async def disconnect(self):
        """Close the connection to the MCP server."""
        await self.exit_stack.aclose()
        self.session = None
        self.stdio = None
        self.write = None
        logger.info("Disconnected from MCP server")
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool on the MCP server.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            The tool's response
        """
        if not self.session:
            raise RuntimeError("Not connected to MCP server")
            
        result = await self.session.call_tool(tool_name, arguments)
        return result
    
    async def read_resource(self, resource_path: str) -> Any:
        """Read a resource from the MCP server.
        
        Args:
            resource_path: Path to the resource
            
        Returns:
            The resource data
        """
        if not self.session:
            raise RuntimeError("Not connected to MCP server")
            
        result = await self.session.read_resource(resource_path)
        return result
    
    async def get_prompt(self, prompt_name: str, arguments: Dict[str, Any]) -> Any:
        """Get a prompt from the MCP server.
        
        Args:
            prompt_name: Name of the prompt
            arguments: Prompt arguments
            
        Returns:
            The prompt template
        """
        if not self.session:
            raise RuntimeError("Not connected to MCP server")
            
        result = await self.session.get_prompt(prompt_name, arguments)
        return result
