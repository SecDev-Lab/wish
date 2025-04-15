"""Configuration for the command generation client."""

import os

from pydantic import BaseModel, Field


class ClientConfig(BaseModel):
    """Configuration class for the command generation client."""

    api_base_url: str = Field(
        default_factory=lambda: os.environ.get("WISH_API_BASE_URL", "http://localhost:3000"),
        description="Base URL of the wish-command-generation-api service"
    )

    @property
    def generate_endpoint(self) -> str:
        """Get the full URL for the generate endpoint."""
        return f"{self.api_base_url.rstrip('/')}/generate"

    @classmethod
    def from_env(cls) -> "ClientConfig":
        """Load configuration from environment variables."""
        return cls()
