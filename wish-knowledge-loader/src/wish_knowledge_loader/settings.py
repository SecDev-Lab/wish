"""Settings for the knowledge loader package."""

import os
from pathlib import Path

from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Wish home directory
    WISH_HOME: str = Field(os.path.join(os.path.expanduser("~"), ".wish"))

    # OpenAI API settings
    OPENAI_API_KEY: str = Field(...)
    OPENAI_MODEL: str = Field("text-embedding-3-small")

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow",  # Allow additional fields
    )

    @property
    def knowledge_dir(self) -> Path:
        """Path to the knowledge directory."""
        return Path(self.WISH_HOME) / "knowledge"

    @property
    def repo_dir(self) -> Path:
        """Path to the repository directory."""
        return self.knowledge_dir / "repo"

    @property
    def db_dir(self) -> Path:
        """Path to the vector database directory."""
        return self.knowledge_dir / "db"

    @property
    def meta_path(self) -> Path:
        """Path to the metadata file."""
        return self.knowledge_dir / "meta.json"


# Create a singleton instance
settings = Settings()
