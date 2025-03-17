"""Factory for Settings."""

import factory

from wish_models.settings import Settings


class SettingsFactory(factory.Factory):
    """Factory for Settings."""

    class Meta:
        model = Settings

    # テスト用のデフォルト値
    OPENAI_API_KEY = "sk-dummy-key-for-testing"
    OPENAI_MODEL = "gpt-4o-mini"
    WISH_HOME = "/tmp/wish-test-home"

    # Embedding model settings
    OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
    EMBEDDING_MODEL = "text-embedding-3-small"

    # LangSmith settings
    LANGCHAIN_TRACING_V2 = False  # テスト時はトレースを無効化
    LANGCHAIN_ENDPOINT = "https://api.smith.langchain.com"
    LANGCHAIN_API_KEY = "ls-dummy-key-for-testing"
    LANGCHAIN_PROJECT = "wish-test"
