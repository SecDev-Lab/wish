import os
from unittest.mock import patch

from wish_sh.settings import Settings


class TestSettings:
    def test_initialization_with_default(self):
        """Test that Settings initializes with the default WISH_HOME when environment variable is not set."""
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "test-api-key",  # Required field
            "OPENAI_MODEL": "test-model",      # Optional but providing for completeness
        }, clear=True):
            settings = Settings()
            expected_default = os.path.join(os.path.expanduser("~"), ".wish")
            assert settings.wish_home == expected_default
            assert settings.WISH_HOME == expected_default  # Test property
            assert settings.openai_api_key == "test-api-key"
            assert settings.openai_model == "test-model"

    def test_initialization_with_env_var(self):
        """Test that Settings initializes with the WISH_HOME from environment variable when it is set."""
        custom_wish_home = "/custom/wish/home"
        with patch.dict(os.environ, {
            "WISH_HOME": custom_wish_home,
            "OPENAI_API_KEY": "test-api-key",  # Required field
            "OPENAI_MODEL": "test-model",      # Optional but providing for completeness
        }, clear=True):
            settings = Settings()
            assert settings.wish_home == custom_wish_home
            assert settings.WISH_HOME == custom_wish_home  # Test property
            assert settings.openai_api_key == "test-api-key"
            assert settings.openai_model == "test-model"
