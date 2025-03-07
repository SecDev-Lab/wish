import os

from pydantic import ConfigDict, Field, field_validator
from pydantic_settings import BaseSettings

# Constants
DEFAULT_WISH_HOME = os.path.join(os.path.expanduser("~"), ".wish")


class Settings(BaseSettings):
    """Application settings."""

    # Wish home directory
    wish_home: str = Field(DEFAULT_WISH_HOME, validation_alias="WISH_HOME")

    # OpenAI API settings
    openai_api_key: str = Field(..., validation_alias="OPENAI_API_KEY")
    openai_model: str = Field("gpt-4o", validation_alias="OPENAI_MODEL")

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra='allow'  # Allow additional fields
    )

    # Validate wish_home value and expand ~ if present
    @field_validator('wish_home')
    def expand_home_dir(cls, v):
        if v.startswith('~'):
            return os.path.expanduser(v)
        return v

    # Add WISH_HOME property for backward compatibility
    @property
    def WISH_HOME(self) -> str:
        """Get WISH_HOME for backward compatibility."""
        return self.wish_home
