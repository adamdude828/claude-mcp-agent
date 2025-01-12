"""Tests for configuration file handling."""
import json
import pytest
from clade_mcp_agent.config_handler import ConfigHandler, ConfigLoadError

@pytest.fixture
def temp_config_file(tmp_path):
    """Create a temporary config file."""
    config = {
        "servers": {
            "test_server": {
                "host": "localhost",
                "port": 8080,
                "server_path": "${TEST_SERVER_PATH}",
                "env_vars": {
                    "DEBUG": "true",
                    "API_KEY": "${TEST_API_KEY}"
                }
            }
        }
    }
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(config))
    return config_file

@pytest.fixture
def temp_base_config(tmp_path):
    """Create a temporary base config file."""
    config = {
        "servers": {
            "base_server": {
                "host": "base.local",
                "port": 9090,
                "server_path": "/base/path",
                "env_vars": {
                    "BASE_VAR": "base_value"
                }
            }
        }
    }
    config_file = tmp_path / "base_config.json"
    config_file.write_text(json.dumps(config))
    return config_file

def test_load_config(temp_config_file):
    """Test basic config loading."""
    handler = ConfigHandler()
    config = handler.load_config(temp_config_file)
    
    assert "servers" in config
    assert "test_server" in config["servers"]
    assert config["servers"]["test_server"]["host"] == "localhost"
    assert config["servers"]["test_server"]["port"] == 8080

def test_env_var_substitution(temp_config_file, monkeypatch):
    """Test environment variable substitution."""
    monkeypatch.setenv("TEST_SERVER_PATH", "/test/server")
    monkeypatch.setenv("TEST_API_KEY", "secret_key")
    
    handler = ConfigHandler()
    config = handler.load_config(temp_config_file)
    
    server_config = config["servers"]["test_server"]
    assert server_config["server_path"] == "/test/server"
    assert server_config["env_vars"]["API_KEY"] == "secret_key"

def test_config_merge(temp_base_config, temp_config_file):
    """Test merging of base and overlay configs."""
    handler = ConfigHandler(base_config_path=temp_base_config)
    config = handler.load_config(temp_config_file)
    
    assert "base_server" in config["servers"]
    assert "test_server" in config["servers"]
    assert config["servers"]["base_server"]["port"] == 9090
    assert config["servers"]["test_server"]["port"] == 8080

def test_invalid_json(tmp_path):
    """Test handling of invalid JSON."""
    invalid_file = tmp_path / "invalid.json"
    invalid_file.write_text("{invalid json")
    
    handler = ConfigHandler()
    with pytest.raises(ConfigLoadError) as exc_info:
        handler.load_config(invalid_file)
    assert "Invalid JSON" in str(exc_info.value)

def test_missing_file():
    """Test handling of missing config file."""
    handler = ConfigHandler()
    with pytest.raises(ConfigLoadError) as exc_info:
        handler.load_config("/nonexistent/config.json")
    assert "not found" in str(exc_info.value)

def test_load_server_configs(temp_config_file, monkeypatch, tmp_path):
    """Test loading and validation of server configs."""
    # Create executable server file
    server_path = tmp_path / "test_server"
    server_path.touch(mode=0o755)
    monkeypatch.setenv("TEST_SERVER_PATH", str(server_path))
    monkeypatch.setenv("TEST_API_KEY", "test_key")
    
    handler = ConfigHandler()
    server_configs = handler.load_server_configs(temp_config_file)
    
    assert "test_server" in server_configs
    config = server_configs["test_server"]
    assert config.host == "localhost"
    assert config.port == 8080
    assert config.server_path == server_path
    assert config.env_vars["DEBUG"] == "true"
    assert config.env_vars["API_KEY"] == "test_key"

def test_invalid_server_config(temp_config_file):
    """Test handling of invalid server configuration."""
    # Modify config to be invalid
    with temp_config_file.open() as f:
        config = json.load(f)
    config["servers"]["test_server"]["port"] = -1  # Invalid port
    temp_config_file.write_text(json.dumps(config))
    
    handler = ConfigHandler()
    with pytest.raises(ConfigLoadError) as exc_info:
        handler.load_server_configs(temp_config_file)
    assert "Invalid config for server" in str(exc_info.value)

def test_no_servers_section(tmp_path):
    """Test handling of config without servers section."""
    empty_config = tmp_path / "empty.json"
    empty_config.write_text("{}")
    
    handler = ConfigHandler()
    with pytest.raises(ConfigLoadError) as exc_info:
        handler.load_server_configs(empty_config)
    assert "No 'servers' section" in str(exc_info.value)

def test_deep_merge(tmp_path):
    """Test deep merging of nested configurations."""
    base_config = {
        "servers": {
            "server1": {
                "host": "base.local",
                "env_vars": {
                    "BASE_VAR": "base",
                    "SHARED_VAR": "base_value"
                }
            }
        }
    }
    overlay_config = {
        "servers": {
            "server1": {
                "host": "overlay.local",
                "env_vars": {
                    "OVERLAY_VAR": "overlay",
                    "SHARED_VAR": "overlay_value"
                }
            }
        }
    }
    
    base_file = tmp_path / "base.json"
    overlay_file = tmp_path / "overlay.json"
    base_file.write_text(json.dumps(base_config))
    overlay_file.write_text(json.dumps(overlay_config))
    
    handler = ConfigHandler(base_config_path=base_file)
    config = handler.load_config(overlay_file)
    
    server1 = config["servers"]["server1"]
    assert server1["host"] == "overlay.local"  # Overlay wins
    assert server1["env_vars"]["BASE_VAR"] == "base"  # From base
    assert server1["env_vars"]["OVERLAY_VAR"] == "overlay"  # From overlay
    assert server1["env_vars"]["SHARED_VAR"] == "overlay_value"  # Overlay wins 
