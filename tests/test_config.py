"""Tests for configuration management."""
import os
import pytest
from clade_mcp_agent.config import ServerConfig, Settings

@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Setup test environment variables."""
    monkeypatch.setenv("CLAUDE_API_KEY", "test_key")
    monkeypatch.setenv("MCP_SERVERS", '["server1", "server2"]')  # Just server identifiers
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

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

@pytest.fixture
def temp_symlink(temp_server_file, tmp_path):
    """Create a temporary symlink."""
    symlink_path = tmp_path / "server_link"
    symlink_path.symlink_to(temp_server_file)
    return symlink_path

def test_path_edge_cases(temp_server_file, temp_symlink, tmp_path):
    """Test path handling edge cases."""
    # Test symlink resolution
    config = ServerConfig(
        host="localhost",
        server_path=temp_symlink
    )
    assert config.server_path.resolve() == temp_server_file.resolve()

    # Test relative paths
    rel_path = os.path.relpath(temp_server_file, tmp_path)
    with pytest.raises(ValueError):
        ServerConfig(
            host="localhost",
            server_path=rel_path
        )

    # Test permission scenarios
    no_exec = tmp_path / "no_exec"
    no_exec.touch(mode=0o644)
    with pytest.raises(ValueError) as exc_info:
        ServerConfig(
            host="localhost",
            server_path=no_exec
        )
    assert "not executable" in str(exc_info.value)

def test_complex_serialization(temp_server_file, tmp_path):
    """Test complex object serialization."""
    config = ServerConfig(
        host="localhost",
        port=8080,
        server_path=temp_server_file,
        working_dir=tmp_path,
        env_vars={
            "PATH": "/usr/local/bin:/usr/bin",
            "DEBUG": "true",
            "SPECIAL": "value with spaces and $pecial chars"
        }
    )
    
    # Test serialization
    json_data = config.model_dump_json()
    
    # Verify all fields are properly serialized
    assert str(temp_server_file) in json_data
    assert str(tmp_path) in json_data
    assert "/usr/local/bin:/usr/bin" in json_data
    assert "value with spaces and $pecial chars" in json_data
    assert "localhost" in json_data
    assert "8080" in json_data

    # Test deserialization
    import json
    data = json.loads(json_data)
    reconstructed = ServerConfig(
        host=data["host"],
        port=data["port"],
        server_path=data["server_path"],
        working_dir=data["working_dir"],
        env_vars=data["env_vars"]
    )
    
    assert reconstructed.server_path == config.server_path
    assert reconstructed.working_dir == config.working_dir
    assert reconstructed.env_vars == config.env_vars
    assert reconstructed.host == config.host
    assert reconstructed.port == config.port

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

def test_default_values(temp_server_file):
    """Test default values in server configuration."""
    config = ServerConfig(
        host="localhost",
        server_path=temp_server_file
    )
    assert config.host == "localhost"
    assert config.port == 8080  # Default port
    assert config.config_path is None
    assert config.working_dir is None
    assert config.env_vars == {}

def test_invalid_server_path():
    """Test validation of non-existent server path."""
    with pytest.raises(ValueError) as exc_info:
        ServerConfig(
            host="localhost",
            server_path="/nonexistent/path/to/server"
        )
    assert "Server executable not found" in str(exc_info.value)

def test_invalid_config_path(temp_server_file):
    """Test validation of non-existent config path."""
    with pytest.raises(ValueError) as exc_info:
        ServerConfig(
            host="localhost",
            server_path=temp_server_file,
            config_path="/nonexistent/config.json"
        )
    assert "Config file not found" in str(exc_info.value)

def test_invalid_working_dir(temp_server_file):
    """Test validation of non-existent working directory."""
    with pytest.raises(ValueError) as exc_info:
        ServerConfig(
            host="localhost",
            server_path=temp_server_file,
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
    json_data = config.model_dump_json()
    assert str(temp_server_file) in json_data
    assert "localhost" in json_data

def test_settings_from_env():
    """Test loading settings from environment variables."""
    settings = Settings()
    assert settings.claude_api_key == "test_key"
    assert settings.mcp_servers == ["server1", "server2"]
    assert settings.log_level == "DEBUG" 