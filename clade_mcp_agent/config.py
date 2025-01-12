"""Configuration management for the Clade MCP Agent."""
import os
from pathlib import Path
from typing import List, Optional
from pydantic import BaseSettings, BaseModel, validator, Field

class ServerConfig(BaseModel):
    """Configuration for a single MCP server."""
    host: str = Field(..., description="Server hostname or IP address")
    port: int = Field(default=8080, description="Server port")
    server_path: Path = Field(..., description="Path to server executable")
    config_path: Optional[Path] = Field(None, description="Path to server config file")
    working_dir: Optional[Path] = Field(None, description="Working directory for server")
    env_vars: dict[str, str] = Field(default_factory=dict, description="Environment variables for server")

    @validator('server_path', 'config_path', 'working_dir')
    def validate_paths(cls, v: Optional[Path], field: str) -> Optional[Path]:
        """Validate that paths exist and are accessible."""
        if v is None:
            return v
        
        # Expand environment variables in path
        path_str = os.path.expandvars(str(v))
        path = Path(path_str).resolve()

        if field.name == 'server_path':
            if not path.exists():
                raise ValueError(f"Server executable not found at: {path}")
            if not os.access(path, os.X_OK):
                raise ValueError(f"Server executable is not executable: {path}")
        elif field.name == 'config_path' and not path.exists():
            raise ValueError(f"Config file not found at: {path}")
        elif field.name == 'working_dir' and not path.is_dir():
            raise ValueError(f"Working directory does not exist: {path}")

        return path

    class Config:
        """Pydantic config."""
        json_encoders = {
            Path: str
        }

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    claude_api_key: str
    mcp_servers: List[str]
    log_level: str = "INFO"

    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = False

        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str) -> any:
            """Parse environment variables."""
            if field_name == "mcp_servers":
                return raw_val.split(",")
            return raw_val

settings = Settings()
