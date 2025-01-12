"""Claude API client implementation."""
from typing import Dict, Any
from anthropic import Anthropic


class ClaudeClient:
    """Client for interacting with Claude API."""
    
    def __init__(self, api_key: str):
        """Initialize the Claude client.
        
        Args:
            api_key: The Claude API key to use for authentication
        """
        self.client = Anthropic(api_key=api_key)
    
    async def process_message(
        self, message: str, context: Dict[str, Any]
    ) -> str:
        """Process a message with context through Claude.
        
        Args:
            message: The message to process
            context: Additional context for Claude
            
        Returns:
            The response from Claude
        """
        raise NotImplementedError('Message processing not yet implemented')
