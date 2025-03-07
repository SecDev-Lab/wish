"""Factory for Settings."""


import factory

from wish_sh.settings import Settings


class SettingsFactory(factory.Factory):
    """Factory for Settings."""

    class Meta:
        model = Settings

    # テスト用のデフォルト値
    openai_api_key = "sk-dummy-key-for-testing"
    openai_model = "gpt-4o-mini"
    wish_home = "/tmp/wish-test-home"
