"""Common test fixtures and utilities."""
import pytest
from pathlib import Path
from typing import AsyncGenerator
import aiohttp

@pytest.fixture
def test_data_dir() -> Path:
    """Return path to test data directory."""
    return Path(__file__).parent / "data"

@pytest.fixture
def mock_server_config() -> dict:
    """Return a mock server configuration."""
    return {
        "name": "test_server",
        "path": "/path/to/test/server.py",
        "enabled": True,
        "env_vars": {
            "TEST_VAR": "test_value"
        }
    }

@pytest.fixture
async def mock_aiohttp_session() -> AsyncGenerator[aiohttp.ClientSession, None]:
    """Create and yield a mock aiohttp session."""
    async with aiohttp.ClientSession() as session:
        yield session

@pytest.fixture
def mock_mcp_server(monkeypatch):
    """Mock MCP server responses."""
    class MockResponse:
        def __init__(self, data: dict, status: int = 200):
            self._data = data
            self.status = status
            
        async def json(self):
            return self._data
            
        async def __aenter__(self):
            return self
            
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
    
    def mock_post(*args, **kwargs):
        return MockResponse({"status": "success", "response": "test response"})
    
    monkeypatch.setattr("aiohttp.ClientSession.post", mock_post)
    return mock_post 
