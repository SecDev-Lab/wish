import os
from unittest.mock import patch

from wish_sh.settings import Settings


class TestSettings:
    def test_initialization_with_default(self):
        """Test that Settings initializes with the default WISH_HOME when environment variable is not set."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            expected_default = os.path.join(os.path.expanduser("~"), ".wish")
            assert settings.WISH_HOME == expected_default

    def test_initialization_with_env_var(self):
        """Test that Settings initializes with the WISH_HOME from environment variable when it is set."""
        custom_wish_home = "/custom/wish/home"
        with patch.dict(os.environ, {"WISH_HOME": custom_wish_home}, clear=True):
            settings = Settings()
            assert settings.WISH_HOME == custom_wish_home
