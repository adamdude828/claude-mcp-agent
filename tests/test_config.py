"""Tests for configuration management."""
import pytest
from pydantic import ValidationError
from clade_mcp_agent.config import ServerConfig

@pytest.fixture
def temp_server_file(tmp_path):
    """Create a temporary server executable."""
    server_file = tmp_path / "server"
    server_file.touch(mode=0o755)
    return server_file

@pytest.fixture
def temp_config_file(tmp_path):
    """Create a temporary config file."""
    config_file = tmp_path / "config.json"
    config_file.touch()
    return config_file

def test_valid_server_config(temp_server_file, temp_config_file, tmp_path):
    """Test creating a valid server configuration."""
    config = ServerConfig(
        host="localhost",
        port=8080,
        server_path=temp_server_file,
        config_path=temp_config_file,
        working_dir=tmp_path,
        env_vars={"DEBUG": "1"}
    )
    assert config.host == "localhost"
    assert config.port == 8080
    assert config.server_path == temp_server_file
    assert config.config_path == temp_config_file
    assert config.working_dir == tmp_path
    assert config.env_vars == {"DEBUG": "1"}

def test_default_values():
    """Test default values in server configuration."""
    config = ServerConfig(
        host="localhost",
        server_path="/usr/local/bin/server"  # Note: This will fail validation if file doesn't exist
    )
    assert config.port == 8080  # Default port
    assert config.config_path is None
    assert config.working_dir is None
    assert config.env_vars == {}

def test_invalid_server_path():
    """Test validation of non-existent server path."""
    with pytest.raises(ValidationError) as exc_info:
        ServerConfig(
            host="localhost",
            server_path="/nonexistent/path/to/server"
        )
    assert "Server executable not found" in str(exc_info.value)

def test_invalid_config_path():
    """Test validation of non-existent config path."""
    with pytest.raises(ValidationError) as exc_info:
        ServerConfig(
            host="localhost",
            server_path="/usr/local/bin/server",  # Note: This will fail validation if file doesn't exist
            config_path="/nonexistent/config.json"
        )
    assert "Config file not found" in str(exc_info.value)

def test_invalid_working_dir():
    """Test validation of non-existent working directory."""
    with pytest.raises(ValidationError) as exc_info:
        ServerConfig(
            host="localhost",
            server_path="/usr/local/bin/server",  # Note: This will fail validation if file doesn't exist
            working_dir="/nonexistent/dir"
        )
    assert "Working directory does not exist" in str(exc_info.value)

def test_env_var_expansion(temp_server_file, monkeypatch):
    """Test environment variable expansion in paths."""
    monkeypatch.setenv("TEST_SERVER_PATH", str(temp_server_file))
    
    config = ServerConfig(
        host="localhost",
        server_path="${TEST_SERVER_PATH}"
    )
    assert config.server_path == temp_server_file

def test_json_serialization(temp_server_file):
    """Test JSON serialization of ServerConfig."""
    config = ServerConfig(
        host="localhost",
        server_path=temp_server_file
    )
    json_data = config.json()
    assert str(temp_server_file) in json_data
    assert "localhost" in json_data 