"""Factory for Settings."""


import factory

from wish_sh.settings import Settings


class SettingsFactory(factory.Factory):
    """Factory for Settings."""

    class Meta:
        model = Settings

    # テスト用のデフォルト値
    OPENAI_API_KEY = "sk-dummy-key-for-testing"
    OPENAI_MODEL = "gpt-4o-mini"
    WISH_HOME = "/tmp/wish-test-home"

