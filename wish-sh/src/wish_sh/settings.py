import os

from pydantic import ConfigDict, Field, field_validator
from pydantic_settings import BaseSettings

# Constants
DEFAULT_WISH_HOME = os.path.join(os.path.expanduser("~"), ".wish")


class Settings(BaseSettings):
    """Application settings."""

    # Wish home directory
    WISH_HOME: str = Field(DEFAULT_WISH_HOME)

    # OpenAI API settings
    OPENAI_API_KEY: str = Field(...)
    OPENAI_MODEL: str = Field("gpt-4o")

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow",  # Allow additional fields
    )

    # Validate wish_home value and expand ~ if present
    @field_validator("WISH_HOME")
    def expand_home_dir(cls, v):
        if v.startswith("~"):
            return os.path.expanduser(v)
        return v
