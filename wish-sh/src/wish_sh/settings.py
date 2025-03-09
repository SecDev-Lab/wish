"""Settings for wish-sh package."""

import os

from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings

# Constants
DEFAULT_WISH_HOME = os.path.join(os.path.expanduser("~"), ".wish")

class Settings(BaseSettings):
    """Application settings."""

    # Wish home directory
    WISH_HOME: str = Field(DEFAULT_WISH_HOME)

    # OpenAI API settings
    OPENAI_API_KEY: str = Field(default="sk-test-key" if "PYTEST_CURRENT_TEST" in os.environ else ...)
    OPENAI_MODEL: str = Field("gpt-4o")

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow",  # Allow additional fields
    )
