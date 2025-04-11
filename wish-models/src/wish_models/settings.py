"""Settings for all wish packages."""

import os
from pathlib import Path

from pydantic import ConfigDict, Field, field_validator
from pydantic_settings import BaseSettings

# Constants
DEFAULT_WISH_HOME = os.path.join(os.path.expanduser("~"), ".wish")

class Settings(BaseSettings):
    """Application settings."""

    # クラスレベルでmodel_configを定義
    model_config = ConfigDict(
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow",
    )

    # Wish home directory
    WISH_HOME: str = Field(DEFAULT_WISH_HOME)

    # API settings
    WISH_API_BASE_URL: str = Field("http://localhost:3000")

    # Custom env file path
    ENV_FILE: str | None = Field(None)

    # OpenAI API settings
    OPENAI_API_KEY: str = Field(default="WARNING: Set OPENAI_API_KEY env var or in .env file to use OpenAI features")
    OPENAI_MODEL: str = Field("gpt-4o")

    # Embedding model settings
    OPENAI_EMBEDDING_MODEL: str = Field("text-embedding-3-small")

    # RAG settings (for wish-command-generation)
    EMBEDDING_MODEL: str = Field("text-embedding-3-small")

    # LangSmith settings
    LANGCHAIN_TRACING_V2: bool = Field(True)
    LANGCHAIN_ENDPOINT: str = Field("https://api.smith.langchain.com")
    LANGCHAIN_API_KEY: str = Field(
        default="WARNING: Set LANGCHAIN_API_KEY env var or in .env file to use LangChain features"
    )
    LANGCHAIN_PROJECT: str = Field("wish")

    def __init__(self, env_file: str | None = None, project: str | None = None, **kwargs):
        """Initialize settings with optional custom env file and project.

        Args:
            env_file: Path to custom .env file
            project: Project name for LangSmith
            **kwargs: Additional keyword arguments
        """
        # Get env files to load
        env_files = self._get_env_files(env_file)

        # 環境変数ファイルを設定
        kwargs["_env_file"] = env_files

        # Initialize with kwargs
        super().__init__(**kwargs)

        # Override project if specified
        if project:
            self.LANGCHAIN_PROJECT = project

        # Set environment variables for LangChain/LangGraph
        # NOTE: This modifies process-wide environment variables, which may have side effects:
        # - It affects other code running in the same process
        # - Environment variable changes are inherited by child processes
        # - Be cautious when switching between multiple projects or tracing configurations
        os.environ["LANGCHAIN_TRACING_V2"] = "true" if self.LANGCHAIN_TRACING_V2 else "false"
        os.environ["LANGCHAIN_ENDPOINT"] = self.LANGCHAIN_ENDPOINT
        os.environ["LANGCHAIN_API_KEY"] = self.LANGCHAIN_API_KEY
        os.environ["LANGCHAIN_PROJECT"] = self.LANGCHAIN_PROJECT

    def _get_env_files(self, env_file: str | None = None) -> list[str]:
        """Get list of env files to load."""
        if env_file:
            return [env_file]

        # Default env file in WISH_HOME
        wish_home = os.environ.get("WISH_HOME", DEFAULT_WISH_HOME)
        if wish_home.startswith("~"):
            wish_home = os.path.expanduser(wish_home)

        wish_home_env = os.path.join(wish_home, "env")

        # Project root .env for backward compatibility
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
        project_env = os.path.join(project_root, ".env")

        return [wish_home_env, project_env, ".env"]

    # Knowledge properties
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

    # Validate wish_home value and expand ~ if present
    @field_validator("WISH_HOME")
    def expand_home_dir(cls, v):
        if v.startswith("~"):
            return os.path.expanduser(v)
        return v

# Create default settings instance
settings = Settings()
