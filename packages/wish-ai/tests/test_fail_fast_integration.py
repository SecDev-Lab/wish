"""
Integration tests for fail-fast behavior when configuration is missing.

Tests the complete flow from configuration absence to immediate failure
across the entire application stack.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from wish_core.config.manager import ConfigManager

from wish_ai.gateway import OpenAIGateway
from wish_ai.gateway.base import LLMAuthenticationError


class TestFailFastIntegration:
    """Integration tests for fail-fast behavior."""

    def test_openai_gateway_fails_fast_without_any_configuration(self):
        """Test that OpenAIGateway fails immediately when no API key is configured."""
        with patch.dict(os.environ, {}, clear=True):
            with tempfile.TemporaryDirectory() as temp_dir:
                config_path = Path(temp_dir) / "config.toml"
                config_path.write_text("")

                # Mock the global config manager to use our test config
                with patch("wish_ai.gateway.openai.get_api_key") as mock_get_key:
                    mock_get_key.return_value = None

                    # Should raise LLMAuthenticationError immediately
                    with pytest.raises(LLMAuthenticationError) as exc_info:
                        OpenAIGateway()

                    assert "OpenAI API key not provided" in str(exc_info.value)
                    assert "OPENAI_API_KEY environment variable" in str(exc_info.value)
                    assert "~/.wish/config.toml" in str(exc_info.value)

    def test_openai_gateway_fails_fast_with_empty_environment_variable(self):
        """Test that OpenAIGateway fails when environment variable is empty."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
            with tempfile.TemporaryDirectory() as temp_dir:
                config_path = Path(temp_dir) / "config.toml"
                config_path.write_text("")

                # Mock the global config manager to use our test config
                with patch("wish_ai.gateway.openai.get_api_key") as mock_get_key:
                    mock_get_key.return_value = None

                    # Should raise LLMAuthenticationError immediately
                    with pytest.raises(LLMAuthenticationError) as exc_info:
                        OpenAIGateway()

                    assert "OpenAI API key not provided" in str(exc_info.value)

    def test_openai_gateway_fails_fast_with_empty_config_file(self):
        """Test that OpenAIGateway fails when config file has empty API key."""
        with patch.dict(os.environ, {}, clear=True):
            with tempfile.TemporaryDirectory() as temp_dir:
                config_path = Path(temp_dir) / "config.toml"
                config_path.write_text("""
[llm]
api_key = ""
""")

                # Mock the global config manager to use our test config
                with patch("wish_ai.gateway.openai.get_api_key") as mock_get_key:
                    mock_get_key.return_value = None

                    # Should raise LLMAuthenticationError immediately
                    with pytest.raises(LLMAuthenticationError) as exc_info:
                        OpenAIGateway()

                    assert "OpenAI API key not provided" in str(exc_info.value)

    def test_openai_gateway_succeeds_with_environment_variable(self):
        """Test that OpenAIGateway succeeds when environment variable is set."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-env-key"}):
            with tempfile.TemporaryDirectory() as temp_dir:
                config_path = Path(temp_dir) / "config.toml"
                config_path.write_text("")

                # Mock the global config manager to use our test config
                with patch("wish_ai.gateway.openai.get_api_key") as mock_get_key:
                    mock_get_key.return_value = "test-env-key"

                    # Should succeed without raising exception
                    gateway = OpenAIGateway()
                    assert gateway.api_key == "test-env-key"

    def test_openai_gateway_succeeds_with_config_file(self):
        """Test that OpenAIGateway succeeds when config file has API key."""
        with patch.dict(os.environ, {}, clear=True):
            with tempfile.TemporaryDirectory() as temp_dir:
                config_path = Path(temp_dir) / "config.toml"
                config_path.write_text("""
[llm]
api_key = "test-config-key"
""")

                # Mock the global config manager to use our test config
                with patch("wish_ai.gateway.openai.get_api_key") as mock_get_key:
                    mock_get_key.return_value = "test-config-key"

                    # Should succeed without raising exception
                    gateway = OpenAIGateway()
                    assert gateway.api_key == "test-config-key"

    def test_priority_hierarchy_in_openai_gateway(self):
        """Test that OpenAIGateway respects priority: env var > config file."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "env-key"}):
            with tempfile.TemporaryDirectory() as temp_dir:
                config_path = Path(temp_dir) / "config.toml"
                config_path.write_text("""
[llm]
api_key = "config-key"
""")

                # Mock the global config manager to return env key (higher priority)
                with patch("wish_ai.gateway.openai.get_api_key") as mock_get_key:
                    mock_get_key.return_value = "env-key"

                    # Should use environment variable
                    gateway = OpenAIGateway()
                    assert gateway.api_key == "env-key"

    def test_explicit_api_key_overrides_configuration(self):
        """Test that explicit API key parameter overrides all configuration."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "env-key"}):
            with tempfile.TemporaryDirectory() as temp_dir:
                config_path = Path(temp_dir) / "config.toml"
                config_path.write_text("""
[llm]
api_key = "config-key"
""")

                # Mock the global config manager
                with patch("wish_ai.gateway.openai.get_api_key") as mock_get_key:
                    mock_get_key.return_value = "env-key"

                    # Explicit parameter should override everything
                    gateway = OpenAIGateway(api_key="explicit-key")
                    assert gateway.api_key == "explicit-key"

    def test_no_configuration_produces_helpful_error_message(self):
        """Test that missing configuration produces a helpful error message."""
        with patch.dict(os.environ, {}, clear=True):
            with tempfile.TemporaryDirectory() as temp_dir:
                config_path = Path(temp_dir) / "config.toml"
                config_path.write_text("")

                # Mock the global config manager to use our test config
                with patch("wish_ai.gateway.openai.get_api_key") as mock_get_key:
                    mock_get_key.return_value = None

                    # Should raise with helpful error message
                    with pytest.raises(LLMAuthenticationError) as exc_info:
                        OpenAIGateway()

                    error_message = str(exc_info.value)
                    assert "OpenAI API key not provided" in error_message
                    assert "OPENAI_API_KEY environment variable" in error_message
                    assert "~/.wish/config.toml" in error_message
                    assert exc_info.value.provider == "openai"

    def test_configuration_validation_detects_missing_setup(self):
        """Test that configuration validation correctly identifies missing setup."""
        with patch.dict(os.environ, {}, clear=True):
            with tempfile.TemporaryDirectory() as temp_dir:
                config_path = Path(temp_dir) / "config.toml"
                config_path.write_text("")

                manager = ConfigManager(config_path=config_path)
                result = manager.validate_setup()

                # Should detect missing configuration
                assert result["api_key_configured"] is False
                assert result["api_key_source"] is None
                assert len(result["issues"]) > 0
                assert any("API key" in issue for issue in result["issues"])

    def test_configuration_validation_detects_environment_priority(self):
        """Test that configuration validation correctly identifies environment priority."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "env-key"}):
            with tempfile.TemporaryDirectory() as temp_dir:
                config_path = Path(temp_dir) / "config.toml"
                config_path.write_text("""
[llm]
api_key = "config-key"
""")

                manager = ConfigManager(config_path=config_path)
                result = manager.validate_setup()

                # Should detect environment variable as source
                assert result["api_key_configured"] is True
                assert result["api_key_source"] == "environment"
                assert len(result["issues"]) == 0

    def test_configuration_validation_detects_config_file_fallback(self):
        """Test that configuration validation correctly identifies config file fallback."""
        with patch.dict(os.environ, {}, clear=True):
            with tempfile.TemporaryDirectory() as temp_dir:
                config_path = Path(temp_dir) / "config.toml"
                config_path.write_text("""
[llm]
api_key = "config-key"
""")

                manager = ConfigManager(config_path=config_path)
                result = manager.validate_setup()

                # Should detect config file as source
                assert result["api_key_configured"] is True
                assert result["api_key_source"] == "config_file"
                assert len(result["issues"]) == 0
