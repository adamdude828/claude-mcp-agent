"""Configuration file handling and processing."""
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union
from .config import ServerConfig
from .logging import get_logger

logger = get_logger(__name__)

class ConfigLoadError(Exception):
    """Raised when there is an error loading the configuration."""
    pass

class ConfigHandler:
    """Handles loading and processing of configuration files."""
    
    def __init__(self, base_config_path: Optional[Union[str, Path]] = None):
        """Initialize the config handler.
        
        Args:
            base_config_path: Optional path to base config file
        """
        self.base_config_path = Path(base_config_path) if base_config_path else None
        
    def _substitute_env_vars(self, value: Any) -> Any:
        """Recursively substitute environment variables in strings.
        
        Args:
            value: The value to process
            
        Returns:
            The value with environment variables substituted
        """
        if isinstance(value, str):
            return os.path.expandvars(value)
        elif isinstance(value, dict):
            return {k: self._substitute_env_vars(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._substitute_env_vars(v) for v in value]
        return value

    def _load_json_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Load and parse a JSON configuration file.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            The parsed configuration data
            
        Raises:
            ConfigLoadError: If the file cannot be loaded or parsed
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise ConfigLoadError(f"Config file not found: {file_path}")
                
            with file_path.open() as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigLoadError(f"Invalid JSON in config file {file_path}: {e}")
        except Exception as e:
            raise ConfigLoadError(f"Error loading config file {file_path}: {e}")

    def _merge_configs(self, base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two configuration dictionaries.
        
        Args:
            base: Base configuration
            overlay: Overlay configuration that takes precedence
            
        Returns:
            Merged configuration dictionary
        """
        result = base.copy()
        
        for key, value in overlay.items():
            if (
                key in result and 
                isinstance(result[key], dict) and
                isinstance(value, dict)
            ):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
                
        return result

    def load_config(self, config_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
        """Load and process a configuration file.
        
        Args:
            config_path: Path to the config file to load. If None, uses base_config_path.
            
        Returns:
            The processed configuration dictionary
            
        Raises:
            ConfigLoadError: If there is an error loading the configuration
        """
        # Start with empty config if no base path
        result = {}
        
        # Load base config if it exists
        if self.base_config_path and self.base_config_path.exists():
            try:
                result = self._load_json_file(self.base_config_path)
                logger.debug("Loaded base config", path=str(self.base_config_path))
            except ConfigLoadError as e:
                logger.warning("Failed to load base config", error=str(e))
        
        # Load and merge overlay config if specified
        if config_path:
            try:
                overlay = self._load_json_file(config_path)
                result = self._merge_configs(result, overlay)
                logger.debug("Merged overlay config", path=str(config_path))
            except ConfigLoadError as e:
                logger.error("Failed to load overlay config", error=str(e))
                raise
        
        # Substitute environment variables
        result = self._substitute_env_vars(result)
        
        return result

    def load_server_configs(self, config_path: Optional[Union[str, Path]] = None) -> Dict[str, ServerConfig]:
        """Load and validate server configurations.
        
        Args:
            config_path: Path to the config file to load
            
        Returns:
            Dictionary of server name to validated ServerConfig objects
            
        Raises:
            ConfigLoadError: If there is an error loading or validating configs
        """
        config_data = self.load_config(config_path)
        
        if "servers" not in config_data:
            raise ConfigLoadError("No 'servers' section in config file")
            
        server_configs = {}
        for server_name, server_data in config_data["servers"].items():
            try:
                # Add server name if not in config
                if "host" not in server_data:
                    server_data["host"] = server_name
                    
                server_configs[server_name] = ServerConfig(**server_data)
                logger.debug("Loaded server config", server=server_name)
            except Exception as e:
                logger.error("Invalid server config", 
                           server=server_name,
                           error=str(e))
                raise ConfigLoadError(f"Invalid config for server {server_name}: {e}")
                
        return server_configs 
