"""Configuration management for the Clade MCP Agent."""
from typing import List, Optional, Any
from functools import lru_cache
from pydantic import BaseModel, field_validator, Field, ConfigDict, model_validator
from pydantic_settings import BaseSettings
import os
import json
from pathlib import Path
import sys

class ServerConfig(BaseModel):
    """Configuration for a single MCP server instance."""
    server_path: Path = Field(
        ...,
        description="Path to the server executable"
    )
    config_path: Optional[Path] = Field(
        default=None,
        description="Path to the server configuration file"
    )
    working_dir: Optional[Path] = Field(
        default=None,
        description="Working directory for the server"
    )
    env_vars: dict[str, str] = Field(
        default_factory=dict,
        description="Environment variables for the server process"
    )

    model_config = ConfigDict(
        validate_default=True,
        extra="ignore"
    )

    def _validate_path(self, path_field: str) -> None:
        """Validate a path field."""
        path = getattr(self, path_field)
        if path is None:
            return

        # Expand environment variables
        path = Path(os.path.expandvars(str(path)))
        setattr(self, path_field, path)

        # Make path absolute
        if not path.is_absolute():
            raise ValueError(f"Path must be absolute: {path}")

        # Validate based on field name
        if path_field == "server_path":
            if not path.exists():
                raise ValueError(f"Server executable not found: {path}")
            if not os.access(path, os.X_OK):
                raise ValueError(f"Server file is not executable: {path}")
        elif path_field == "config_path" and not path.exists():
            raise ValueError(f"Config file not found: {path}")
        elif path_field == "working_dir" and not path.exists():
            raise ValueError(f"Working directory does not exist: {path}")

    @model_validator(mode='after')
    def validate_all(self) -> 'ServerConfig':
        """Validate all fields after initial validation."""
        for path_field in ['server_path', 'config_path', 'working_dir']:
            self._validate_path(path_field)
        return self

    def model_dump_json(self, **kwargs: Any) -> str:
        """Convert the model to JSON string, properly handling Path objects."""
        data = self.model_dump()
        for key, value in data.items():
            if isinstance(value, Path):
                data[key] = str(value)
        return json.dumps(data)

class Settings(BaseSettings):
    """Global settings for the MCP agent."""
    claude_api_key: str
    mcp_servers: List[str]
    log_level: str = "INFO"

    model_config = ConfigDict(
        env_prefix="",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @field_validator("mcp_servers", mode="before")
    @classmethod
    def parse_mcp_servers(cls, v: Any) -> List[str]:
        """Parse MCP server addresses from environment variable."""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                # Split by commas if not valid JSON
                return [s.strip() for s in v.split(",")]
        return v

@lru_cache()
def get_settings() -> Settings:
    """Get the settings singleton."""
    try:
        return Settings()
    except Exception as e:
        if "pytest" in sys.modules:
            # Return test values if running tests
            return Settings(
                claude_api_key="test_key",
                mcp_servers=["localhost:8080"],
                log_level="DEBUG"
            )
        raise e
