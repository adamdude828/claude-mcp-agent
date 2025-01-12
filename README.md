# Claude MCP Agent

A flexible Model Context Protocol (MCP) client implementation designed to work with AI agents, with a focus on state management and server configuration.

## Overview

Claude MCP Agent is a Python library that enables AI agents to interact with MCP servers using structured state management. The agent accepts any Pydantic model as its state, allowing for flexible context definition that gets translated into Claude-compatible prompts. This approach enables precise control over what context is available to the agent while maintaining type safety and validation.

### Example State Definition

```python
from pydantic import BaseModel
from typing import List, Optional

class ConversationContext(BaseModel):
    current_task: str
    relevant_facts: List[str]
    user_preferences: dict
    conversation_history: Optional[List[dict]] = []
    
# The agent will intelligently translate this structure 
# into context that Claude can understand
state = ConversationContext(
    current_task="Weather analysis for trip planning",
    relevant_facts=[
        "User is planning a trip to Seattle",
        "Trip dates: June 15-20",
        "Outdoor activities planned"
    ],
    user_preferences={
        "temperature_unit": "celsius",
        "activity_preference": "outdoor"
    }
)

response = await agent.process_query(
    "What should I pack given the weather forecast?",
    state=state
)
```

### Key Features

- **Pure Client Implementation**: Focused solely on client-side MCP functionality for clean separation of concerns
- **Global Server Configuration**: Centralized management of MCP server configurations
- **Flexible Server Selection**: Ability to use all configured servers or specific subsets per client instance
- **Stateful Operation**: Built-in state management that works seamlessly with LangGraph and similar frameworks
- **Type Safety**: Full TypeScript-style typing support for reliable development

## Installation

```bash
pip install claude-mcp-agent  # Not yet published
```

## Quick Start

```python
from claude_mcp_agent import MCPAgent, ServerConfig

# Configure global servers
servers = [
    ServerConfig(
        name="weather",
        path="/path/to/weather/server.py",
        enabled=True
    ),
    ServerConfig(
        name="database",
        path="/path/to/db/server.py",
        enabled=True
    )
]

# Create agent with all servers
agent = MCPAgent(servers=servers)

# Or create with specific servers
agent = MCPAgent(servers=servers, enabled_servers=["weather"])

# Use with state
state = {"context": "Current weather analysis"}
response = await agent.process_query("What's the weather?", state=state)
```

## Server Configuration

Servers can be configured either through a configuration file or programmatically.

### Configuration File

Create a `mcp_config.json` file:

```json
{
  "servers": {
    "weather": {
      "path": "/path/to/weather_server.py",
      "enabled": true,
      "env_vars": {
        "API_KEY": "${WEATHER_API_KEY}",
        "REGION": "us-west-2"
      }
    },
    "database": {
      "path": "/path/to/db_server.py",
      "enabled": true,
      "env_vars": {
        "DB_CONNECTION": "${DB_URL}"
      }
    }
  }
}
```

Then load it in your code:

```python
from claude_mcp_agent import MCPAgent

# Load from default config path (./mcp_config.json)
agent = MCPAgent.from_config()

# Or specify config path
agent = MCPAgent.from_config("/path/to/mcp_config.json")

# Override specific servers from config
agent = MCPAgent.from_config(
    config_path="mcp_config.json",
    enabled_servers=["weather"]  # Only use weather server from config
)
```

### Programmatic Configuration

You can also configure servers programmatically:

```python
from claude_mcp_agent import MCPAgent, ServerConfig

server_configs = [
    ServerConfig(
        name="weather",
        path="/path/to/weather_server.py",
        enabled=True,
        env_vars={"API_KEY": "xxx"}
    )
]

# Use programmatic configuration
agent = MCPAgent(servers=server_configs)
```

### Mixed Configuration

You can combine both approaches:

```python
# Load base configuration from file
agent = MCPAgent.from_config("mcp_config.json")

# Add additional servers programmatically
additional_server = ServerConfig(
    name="new_service",
    path="/path/to/service.py",
    enabled=True
)

agent.add_server(additional_server)
```

## State Management

The agent maintains state between interactions, making it ideal for use with LangGraph:

```python
# Initialize state
state = {
    "context": "Weather analysis",
    "history": []
}

# Process query with state
response = await agent.process_query(
    "What's the weather like?",
    state=state
)

# State is updated with new context
print(state["history"])  # Shows interaction history
```

## Contributing

Contributions are welcome! Please read our Contributing Guide for details on our code of conduct and development process.