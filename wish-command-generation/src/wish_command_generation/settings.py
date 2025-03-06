"""Settings for the command generation package."""

import os
from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict, field_validator

# Constants
DEFAULT_WISH_HOME = os.path.join(os.path.expanduser("~"), ".wish")


class Settings(BaseSettings):
    """Application settings."""
    
    # OpenAI API settings
    openai_api_key: str = Field(..., validation_alias="OPENAI_API_KEY")
    openai_model: str = Field("gpt-4o", validation_alias="OPENAI_MODEL")
    
    # Wish home directory
    wish_home: str = Field(DEFAULT_WISH_HOME, validation_alias="WISH_HOME")
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra='allow'  # 追加のフィールドを許可
    )
    
    # wish_home の値を検証して、~ を展開する
    @field_validator('wish_home')
    def expand_home_dir(cls, v):
        if v.startswith('~'):
            return os.path.expanduser(v)
        return v


# Create a singleton instance
settings = Settings()
    