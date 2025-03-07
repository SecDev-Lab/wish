"""Settings for the command generation package."""

import os

from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # OpenAI API settings
    OPENAI_API_KEY: str = Field(...)
    OPENAI_MODEL: str = Field("gpt-4o")

    # RAG settings
    WISH_HOME: str = Field(os.path.expanduser("~/.wish"))
    EMBEDDING_MODEL: str = Field("text-embedding-3-small")

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow"  # Allow additional fields
    )


# Create a singleton instance
settings = Settings()
