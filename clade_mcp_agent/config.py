"""Configuration management for the Clade MCP Agent."""
from typing import List
from pydantic import BaseSettings

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
