"""Configuration for the log analysis API."""

from pydantic import BaseModel, Field
from wish_models.settings import Settings


class AnalyzerConfig(BaseModel):
    """Configuration class for log analysis"""

    openai_api_key: str = Field(
        default_factory=lambda: Settings().OPENAI_API_KEY,
        description="OpenAI API key"
    )

    openai_model: str = Field(
        default_factory=lambda: Settings().OPENAI_MODEL or "gpt-4o",
        description="OpenAI model to use"
    )

    langchain_project: str = Field(
        default_factory=lambda: Settings().LANGCHAIN_PROJECT or "wish-log-analysis-api",
        description="LangChain project name"
    )

    langchain_tracing_v2: bool = Field(
        default_factory=lambda: Settings().LANGCHAIN_TRACING_V2 or False,
        description="Enable LangChain tracing"
    )

    @classmethod
    def from_env(cls) -> "AnalyzerConfig":
        """Load configuration from environment variables"""
        return cls()
