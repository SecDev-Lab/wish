"""Settings for the log analysis package."""

import os

from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings

# Get absolute path to project root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
ENV_PATH = os.path.join(PROJECT_ROOT, ".env")


class Settings(BaseSettings):
    """Application settings."""

    # OpenAI API settings
    OPENAI_API_KEY: str = Field(...)
    OPENAI_MODEL: str = Field("gpt-4o")

    # LangSmith settings
    LANGCHAIN_TRACING_V2: bool = Field(True)
    LANGCHAIN_ENDPOINT: str = Field("https://api.smith.langchain.com")
    LANGCHAIN_API_KEY: str = Field(...)
    LANGCHAIN_PROJECT: str = Field("wish-log-analysis")

    model_config = ConfigDict(
        env_file=[ENV_PATH, ".env"],
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow",  # Allow additional fields
    )


# Create a singleton instance
settings = Settings()
