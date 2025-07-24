"""
Edge case tests for configuration handling.

Tests various edge cases and error conditions to ensure robust
fail-fast behavior in all scenarios.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from wish_core.config.manager import ConfigManager

from wish_ai.gateway import OpenAIGateway


class TestConfigurationEdgeCases:
    """Edge case tests for configuration handling."""

    def test_whitespace_only_environment_variable(self):
        """Test handling of whitespace-only environment variable."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "   \t\n   "}):
            with tempfile.TemporaryDirectory() as temp_dir:
                config_path = Path(temp_dir) / "config.toml"
                config_path.write_text("")

                # Mock the global config manager to return the whitespace value
                with patch("wish_ai.gateway.openai.get_api_key") as mock_get_key:
                    mock_get_key.return_value = "   \t\n   "

                    # Whitespace-only should be treated as valid (even though it's not useful)
                    gateway = OpenAIGateway()
                    assert gateway.api_key == "   \t\n   "

    def test_whitespace_only_config_file_value(self):
        """Test handling of whitespace-only config file value."""
        with patch.dict(os.environ, {}, clear=True):
            with tempfile.TemporaryDirectory() as temp_dir:
                config_path = Path(temp_dir) / "config.toml"
                config_path.write_text("""
[llm]
api_key = "   \\t\\n   "
""")

                manager = ConfigManager(config_path=config_path)
                result = manager.get_api_key()

                # Whitespace-only config value should be returned as-is
                assert result == "   \t\n   "

    def test_malformed_config_file_handling(self):
        """Test handling of malformed TOML config file."""
        with patch.dict(os.environ, {}, clear=True):
            with tempfile.TemporaryDirectory() as temp_dir:
                config_path = Path(temp_dir) / "config.toml"
                config_path.write_text("""
[llm
api_key = "missing-bracket"
""")

                manager = ConfigManager(config_path=config_path)

                # Should handle malformed config gracefully
                result = manager.get_api_key()
                assert result is None

    def test_config_file_with_no_llm_section(self):
        """Test handling of config file without [llm] section."""
        with patch.dict(os.environ, {}, clear=True):
            with tempfile.TemporaryDirectory() as temp_dir:
                config_path = Path(temp_dir) / "config.toml"
                config_path.write_text("""
[other_section]
some_key = "some_value"
""")

                manager = ConfigManager(config_path=config_path)
                result = manager.get_api_key()

                # Should return None when no [llm] section exists
                assert result is None

    def test_config_file_with_no_api_key_in_llm_section(self):
        """Test handling of config file with [llm] section but no api_key."""
        with patch.dict(os.environ, {}, clear=True):
            with tempfile.TemporaryDirectory() as temp_dir:
                config_path = Path(temp_dir) / "config.toml"
                config_path.write_text("""
[llm]
model = "gpt-4o"
temperature = 0.1
""")

                manager = ConfigManager(config_path=config_path)
                result = manager.get_api_key()

                # Should return None when api_key is not present in [llm] section
                assert result is None

    def test_config_file_permissions_error(self):
        """Test handling of config file with permission errors."""
        with patch.dict(os.environ, {}, clear=True):
            with tempfile.TemporaryDirectory() as temp_dir:
                config_path = Path(temp_dir) / "config.toml"
                config_path.write_text("""
[llm]
api_key = "test-key"
""")

                # Remove read permissions
                config_path.chmod(0o000)

                try:
                    manager = ConfigManager(config_path=config_path)
                    result = manager.get_api_key()

                    # Should handle permission errors gracefully
                    assert result is None
                finally:
                    # Restore permissions for cleanup
                    config_path.chmod(0o600)

    def test_config_directory_does_not_exist(self):
        """Test handling when config directory doesn't exist."""
        with patch.dict(os.environ, {}, clear=True):
            with tempfile.TemporaryDirectory() as temp_dir:
                nonexistent_path = Path(temp_dir) / "nonexistent" / "config.toml"

                # ConfigManager creates the directory, so we test after it's created
                manager = ConfigManager(config_path=nonexistent_path)
                result = manager.get_api_key()

                # Should return None when config file doesn't exist
                assert result is None

    def test_very_long_api_key_values(self):
        """Test handling of very long API key values."""
        long_key = "a" * 10000  # 10KB key

        with patch.dict(os.environ, {"OPENAI_API_KEY": long_key}):
            with tempfile.TemporaryDirectory() as temp_dir:
                config_path = Path(temp_dir) / "config.toml"
                config_path.write_text("")

                # Mock the global config manager to return the long key
                with patch("wish_ai.gateway.openai.get_api_key") as mock_get_key:
                    mock_get_key.return_value = long_key

                    # Should handle very long keys
                    gateway = OpenAIGateway()
                    assert gateway.api_key == long_key

    def test_unicode_characters_in_api_key(self):
        """Test handling of Unicode characters in API key."""
        unicode_key = "test-key-with-unicode-🔑-characters"

        with patch.dict(os.environ, {"OPENAI_API_KEY": unicode_key}):
            with tempfile.TemporaryDirectory() as temp_dir:
                config_path = Path(temp_dir) / "config.toml"
                config_path.write_text("")

                # Mock the global config manager to return the unicode key
                with patch("wish_ai.gateway.openai.get_api_key") as mock_get_key:
                    mock_get_key.return_value = unicode_key

                    # Should handle Unicode characters
                    gateway = OpenAIGateway()
                    assert gateway.api_key == unicode_key

    def test_special_characters_in_api_key(self):
        """Test handling of special characters in API key."""
        special_key = "test-key-with-special-!@#$%^&*()_+-={}[]|\\:;\"'<>?,./"

        with patch.dict(os.environ, {"OPENAI_API_KEY": special_key}):
            with tempfile.TemporaryDirectory() as temp_dir:
                config_path = Path(temp_dir) / "config.toml"
                config_path.write_text("")

                # Mock the global config manager to return the special key
                with patch("wish_ai.gateway.openai.get_api_key") as mock_get_key:
                    mock_get_key.return_value = special_key

                    # Should handle special characters
                    gateway = OpenAIGateway()
                    assert gateway.api_key == special_key

    def test_newline_characters_in_api_key(self):
        """Test handling of newline characters in API key."""
        newline_key = "test-key\\nwith\\nnewlines"

        with patch.dict(os.environ, {"OPENAI_API_KEY": newline_key}):
            with tempfile.TemporaryDirectory() as temp_dir:
                config_path = Path(temp_dir) / "config.toml"
                config_path.write_text("")

                # Mock the global config manager to return the newline key
                with patch("wish_ai.gateway.openai.get_api_key") as mock_get_key:
                    mock_get_key.return_value = newline_key

                    # Should handle newline characters
                    gateway = OpenAIGateway()
                    assert gateway.api_key == newline_key

    def test_config_file_with_comments(self):
        """Test handling of config file with comments."""
        with patch.dict(os.environ, {}, clear=True):
            with tempfile.TemporaryDirectory() as temp_dir:
                config_path = Path(temp_dir) / "config.toml"
                config_path.write_text("""
# This is a comment
[llm]
# Another comment
api_key = "test-key"  # Inline comment
# More comments
""")

                manager = ConfigManager(config_path=config_path)
                result = manager.get_api_key()

                # Should handle comments correctly
                assert result == "test-key"

    def test_multiple_llm_sections_in_config(self):
        """Test handling of multiple [llm] sections in config."""
        with patch.dict(os.environ, {}, clear=True):
            with tempfile.TemporaryDirectory() as temp_dir:
                config_path = Path(temp_dir) / "config.toml"
                config_path.write_text("""
[llm]
api_key = "first-key"

[llm]
api_key = "second-key"
""")

                manager = ConfigManager(config_path=config_path)

                # Should handle multiple sections gracefully (behavior depends on TOML parser)
                result = manager.get_api_key()
                # The result might be None due to invalid TOML, or the last value
                assert result is None or result == "second-key"

    def test_config_file_with_invalid_toml_syntax(self):
        """Test handling of config file with invalid TOML syntax."""
        with patch.dict(os.environ, {}, clear=True):
            with tempfile.TemporaryDirectory() as temp_dir:
                config_path = Path(temp_dir) / "config.toml"
                config_path.write_text("""
[llm]
api_key = "unclosed quote
model = "gpt-4o"
""")

                manager = ConfigManager(config_path=config_path)
                result = manager.get_api_key()

                # Should handle invalid TOML gracefully
                assert result is None

    def test_empty_string_vs_none_distinction(self):
        """Test distinction between empty string and None values."""
        # Test empty string from environment
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
            with tempfile.TemporaryDirectory() as temp_dir:
                config_path = Path(temp_dir) / "config.toml"
                config_path.write_text("""
[llm]
api_key = "config-key"
""")

                manager = ConfigManager(config_path=config_path)
                result = manager.get_api_key()

                # Empty environment variable should fall back to config file
                assert result == "config-key"

        # Test None from environment (no variable set)
        with patch.dict(os.environ, {}, clear=True):
            with tempfile.TemporaryDirectory() as temp_dir:
                config_path = Path(temp_dir) / "config.toml"
                config_path.write_text("""
[llm]
api_key = "config-key"
""")

                manager = ConfigManager(config_path=config_path)
                result = manager.get_api_key()

                # No environment variable should fall back to config file
                assert result == "config-key"
