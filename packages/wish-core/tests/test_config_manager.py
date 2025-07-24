"""
Test cases for ConfigManager.

Tests the configuration management system including priority hierarchy,
fail-fast behavior, and edge cases.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from wish_core.config.manager import ConfigManager


class TestConfigManager:
    """Test cases for ConfigManager."""

    def test_get_api_key_from_environment_variable(self):
        """Test API key retrieval from environment variable (highest priority)."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "env-api-key"}):
            with tempfile.TemporaryDirectory() as temp_dir:
                config_path = Path(temp_dir) / "config.toml"
                config_path.write_text("""
[llm]
api_key = "config-file-key"
""")

                manager = ConfigManager(config_path=config_path)

                # Environment variable should take precedence
                assert manager.get_api_key() == "env-api-key"

    def test_get_api_key_from_config_file_when_no_env_var(self):
        """Test API key retrieval from config file when no environment variable."""
        with patch.dict(os.environ, {}, clear=True):
            with tempfile.TemporaryDirectory() as temp_dir:
                config_path = Path(temp_dir) / "config.toml"
                config_path.write_text("""
[llm]
api_key = "config-file-key"
""")

                manager = ConfigManager(config_path=config_path)

                # Should fall back to config file
                assert manager.get_api_key() == "config-file-key"

    def test_get_api_key_returns_none_when_no_configuration(self):
        """Test API key returns None when no configuration is available."""
        with patch.dict(os.environ, {}, clear=True):
            with tempfile.TemporaryDirectory() as temp_dir:
                config_path = Path(temp_dir) / "config.toml"
                # Create empty config file
                config_path.write_text("")

                manager = ConfigManager(config_path=config_path)

                # Should return None when no API key is configured
                assert manager.get_api_key() is None

    def test_get_api_key_returns_none_when_config_file_missing(self):
        """Test API key returns None when config file doesn't exist."""
        with patch.dict(os.environ, {}, clear=True):
            with tempfile.TemporaryDirectory() as temp_dir:
                config_path = Path(temp_dir) / "nonexistent.toml"

                manager = ConfigManager(config_path=config_path)

                # Should return None when config file doesn't exist
                assert manager.get_api_key() is None

    def test_get_api_key_handles_empty_environment_variable(self):
        """Test API key handling when environment variable is empty."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
            with tempfile.TemporaryDirectory() as temp_dir:
                config_path = Path(temp_dir) / "config.toml"
                config_path.write_text("""
[llm]
api_key = "config-file-key"
""")

                manager = ConfigManager(config_path=config_path)

                # Empty environment variable should fall back to config file
                assert manager.get_api_key() == "config-file-key"

    def test_get_api_key_handles_whitespace_environment_variable(self):
        """Test API key handling when environment variable contains only whitespace."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "   "}):
            with tempfile.TemporaryDirectory() as temp_dir:
                config_path = Path(temp_dir) / "config.toml"
                config_path.write_text("""
[llm]
api_key = "config-file-key"
""")

                manager = ConfigManager(config_path=config_path)

                # Whitespace-only environment variable should still take precedence
                assert manager.get_api_key() == "   "

    def test_get_api_key_handles_empty_config_file_value(self):
        """Test API key handling when config file has empty API key."""
        with patch.dict(os.environ, {}, clear=True):
            with tempfile.TemporaryDirectory() as temp_dir:
                config_path = Path(temp_dir) / "config.toml"
                config_path.write_text("""
[llm]
api_key = ""
""")

                manager = ConfigManager(config_path=config_path)

                # Empty config file value should return None
                assert manager.get_api_key() is None

    def test_priority_hierarchy_env_over_config(self):
        """Test that environment variable always takes precedence over config file."""
        test_cases = [
            ("env-key", "config-key", "env-key"),
            ("env-key", "", "env-key"),
            ("", "config-key", "config-key"),
            ("", "", None),
        ]

        for env_val, config_val, expected in test_cases:
            with patch.dict(os.environ, {"OPENAI_API_KEY": env_val} if env_val else {}, clear=True):
                with tempfile.TemporaryDirectory() as temp_dir:
                    config_path = Path(temp_dir) / "config.toml"
                    if config_val:
                        config_path.write_text(f"""
[llm]
api_key = "{config_val}"
""")
                    else:
                        config_path.write_text("""
[llm]
""")

                    manager = ConfigManager(config_path=config_path)
                    result = manager.get_api_key()

                    if expected is None:
                        assert result is None
                    else:
                        assert result == expected

    def test_validate_setup_with_various_configurations(self):
        """Test validate_setup method with different configuration states."""
        # Test with environment variable
        with patch.dict(os.environ, {"OPENAI_API_KEY": "env-key"}):
            with tempfile.TemporaryDirectory() as temp_dir:
                config_path = Path(temp_dir) / "config.toml"
                config_path.write_text("")

                manager = ConfigManager(config_path=config_path)
                result = manager.validate_setup()

                assert result["api_key_configured"] is True
                assert result["api_key_source"] == "environment"
                assert len(result["issues"]) == 0

        # Test with config file
        with patch.dict(os.environ, {}, clear=True):
            with tempfile.TemporaryDirectory() as temp_dir:
                config_path = Path(temp_dir) / "config.toml"
                config_path.write_text("""
[llm]
api_key = "config-key"
""")

                manager = ConfigManager(config_path=config_path)
                result = manager.validate_setup()

                assert result["api_key_configured"] is True
                assert result["api_key_source"] == "config_file"
                assert len(result["issues"]) == 0

        # Test with no configuration
        with patch.dict(os.environ, {}, clear=True):
            with tempfile.TemporaryDirectory() as temp_dir:
                config_path = Path(temp_dir) / "config.toml"
                config_path.write_text("")

                manager = ConfigManager(config_path=config_path)
                result = manager.validate_setup()

                assert result["api_key_configured"] is False
                assert result["api_key_source"] is None
                assert len(result["issues"]) > 0
