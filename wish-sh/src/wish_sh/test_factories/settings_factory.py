"""Factory for Settings."""

import os
from pathlib import Path

import factory
from pydantic import ValidationError

from wish_sh.settings import Settings


class SettingsFactory(factory.Factory):
    """Factory for Settings."""

    class Meta:
        model = Settings

    # テスト用のデフォルト値
    openai_api_key = "sk-dummy-key-for-testing"
    openai_model = "gpt-4o"
    wish_home = "/tmp/wish-test-home"

    @classmethod
    def create(cls, **kwargs):
        """Create a Settings instance for testing.
        
        If OPENAI_API_KEY is not provided in kwargs or environment,
        a dummy value will be used.
        """
        # 環境変数から値を取得（あれば）
        defaults = {}
        for key in ["openai_api_key", "openai_model", "wish_home"]:
            env_key = key.upper()
            if env_key in os.environ:
                defaults[key] = os.environ[env_key]
        
        # kwargsで指定された値で上書き
        defaults.update(kwargs)
        
        try:
            return Settings(**defaults)
        except ValidationError:
            # 検証エラーが発生した場合はデフォルト値を使用
            return Settings(
                openai_api_key=cls.openai_api_key,
                openai_model=cls.openai_model,
                wish_home=cls.wish_home,
                **{k: v for k, v in defaults.items() if k not in ["openai_api_key", "openai_model", "wish_home"]}
            )
