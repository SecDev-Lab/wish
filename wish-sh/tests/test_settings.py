import os
from unittest.mock import patch

from wish_sh.settings import Settings


class TestSettings:
    def test_initialization_with_default(self):
        """Test that Settings initializes with the default WISH_HOME when environment variable is not set."""
        with patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "test-api-key",  # Required field
                "OPENAI_MODEL": "test-model",  # Optional but providing for completeness
            },
            clear=True,
        ):
            settings = Settings()
            expected_default = os.path.join(os.path.expanduser("~"), ".wish")
            assert settings.WISH_HOME == expected_default
            assert settings.WISH_HOME == expected_default  # Test property
            assert settings.OPENAI_API_KEY == "test-api-key"
            assert settings.OPENAI_MODEL == "test-model"

    def test_initialization_with_env_var(self):
        """Test that Settings initializes with the WISH_HOME from environment variable when it is set."""
        custom_wish_home = "/custom/wish/home"
        with patch.dict(
            os.environ,
            {
                "WISH_HOME": custom_wish_home,
                "OPENAI_API_KEY": "test-api-key",  # Required field
                "OPENAI_MODEL": "test-model",  # Optional but providing for completeness
            },
            clear=True,
        ):
            settings = Settings()
            assert settings.WISH_HOME == custom_wish_home
            assert settings.WISH_HOME == custom_wish_home  # Test property
            assert settings.OPENAI_API_KEY == "test-api-key"
            assert settings.OPENAI_MODEL == "test-model"

    def test_initialization_from_env_file(self, tmp_path):
        """Test that Settings initializes with values from .env file."""
        # 一時的な .env ファイルを作成
        env_file = tmp_path / ".env"
        env_file.write_text(
            "OPENAI_API_KEY=sk-test-env-file-key\nOPENAI_MODEL=gpt-4-turbo\nWISH_HOME=/custom/env/file/path\n"
        )

        # 環境変数をクリア
        with patch.dict(os.environ, {}, clear=True):
            # .env ファイルのパスを指定して Settings をインスタンス化
            settings = Settings(_env_file=str(env_file))

            # .env ファイルから読み込まれた値を検証
            assert settings.OPENAI_API_KEY == "sk-test-env-file-key"
            assert settings.OPENAI_MODEL == "gpt-4-turbo"
            assert settings.WISH_HOME == "/custom/env/file/path"
