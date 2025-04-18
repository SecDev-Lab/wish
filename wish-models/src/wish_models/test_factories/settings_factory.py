"""Factory for Settings."""

from pathlib import Path

import factory

from wish_models.settings import Settings


class SettingsFactory(factory.Factory):
    """Factory for Settings."""

    class Meta:
        model = Settings

    # Test default values
    OPENAI_API_KEY = "sk-dummy-key-for-testing"
    OPENAI_MODEL = "gpt-4o-mini"
    WISH_HOME = Path("/tmp/wish-test-home")

    # Embedding model settings
    OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
    EMBEDDING_MODEL = "text-embedding-3-small"

    # LangSmith settings
    LANGCHAIN_TRACING_V2 = False  # Disable tracing in tests
    LANGCHAIN_ENDPOINT = "https://api.smith.langchain.com"
    LANGCHAIN_API_KEY = "ls-dummy-key-for-testing"
    LANGCHAIN_PROJECT = "wish-test"
