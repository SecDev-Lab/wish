"""Settings for all wish packages."""

import os
from pathlib import Path
from typing import Optional

from pydantic import ConfigDict, Field, field_validator
from pydantic_settings import BaseSettings

# Constants
DEFAULT_WISH_HOME = Path.home() / ".wish"


def get_default_env_path() -> Path:
    """Get the default env file path (WISH_HOME/env).

    Returns:
        Path to the default env file
    """
    wish_home_str = os.environ.get("WISH_HOME", str(DEFAULT_WISH_HOME))
    wish_home = Path(os.path.expanduser(wish_home_str))
    return wish_home / "env"


class Settings(BaseSettings):
    """Application settings."""

    # Class-level model configuration
    model_config = ConfigDict(
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow",
    )

    # Wish home directory
    WISH_HOME: Path = Field(DEFAULT_WISH_HOME)

    # API settings
    WISH_API_BASE_URL: str = Field("http://localhost:3000")

    # OpenAI API settings
    OPENAI_API_KEY: str = Field(default="WARNING: Set OPENAI_API_KEY env var or in .env file to use OpenAI features")
    OPENAI_MODEL: str = Field("gpt-4o")

    # Embedding model settings
    OPENAI_EMBEDDING_MODEL: str = Field("text-embedding-3-small")

    # RAG settings (for wish-command-generation)
    EMBEDDING_MODEL: str = Field("text-embedding-3-small")
    VECTOR_STORE_TYPE: str = Field("chroma")  # "chroma" or "qdrant"

    # Qdrant settings (optional)
    QDRANT_HOST: str = Field("localhost")
    QDRANT_PORT: int = Field(6333)
    QDRANT_COLLECTION_NAME: str = Field("wish")

    # LangSmith settings
    LANGCHAIN_TRACING_V2: bool = Field(True)
    LANGCHAIN_ENDPOINT: str = Field("https://api.smith.langchain.com")
    LANGCHAIN_API_KEY: str = Field(
        default="WARNING: Set LANGCHAIN_API_KEY env var or in .env file to use LangChain features"
    )
    LANGCHAIN_PROJECT: str = Field("wish")

    def __init__(self, env_file: Optional[Path] = None, project: Optional[str] = None, **kwargs):
        """Initialize settings with optional custom env file and project.

        Args:
            env_file: Path to custom .env file
            project: Project name for LangSmith
            **kwargs: Additional keyword arguments
        """
        # Initialize with kwargs
        # Note: BaseSettings automatically loads values from environment variables
        if env_file is not None and env_file.exists():
            # Pass env_file directly to BaseSettings
            super().__init__(_env_file=str(env_file), **kwargs)
        else:
            super().__init__(**kwargs)

        # Override project if specified
        if project:
            self.LANGCHAIN_PROJECT = project

    # Knowledge properties
    @property
    def knowledge_dir(self) -> Path:
        """Path to the knowledge directory."""
        return self.WISH_HOME / "knowledge"

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

    # Validate wish_home value and convert to Path if needed
    @field_validator("WISH_HOME")
    def ensure_path(cls, v):
        """Ensure WISH_HOME is a Path object and expand ~ if present."""
        if isinstance(v, str):
            return Path(os.path.expanduser(v))
        return v
