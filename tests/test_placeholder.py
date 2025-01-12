"""Basic tests to verify test infrastructure is working."""
import pytest
from pathlib import Path

def test_test_data_dir(test_data_dir):
    """Verify test data directory exists and contains expected files."""
    assert isinstance(test_data_dir, Path)
    assert test_data_dir.exists()
    assert (test_data_dir / "test_config.json").exists()

def test_mock_server_config(mock_server_config):
    """Verify mock server configuration fixture works."""
    assert isinstance(mock_server_config, dict)
    assert mock_server_config["name"] == "test_server"
    assert mock_server_config["enabled"] is True

@pytest.mark.asyncio
async def test_mock_mcp_server(mock_mcp_server, mock_aiohttp_session):
    """Verify mock MCP server fixture works."""
    async with mock_aiohttp_session.post("/test") as response:
        data = await response.json()
        assert data["status"] == "success"
        assert data["response"] == "test response" 
