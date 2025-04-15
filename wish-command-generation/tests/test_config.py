"""Tests for the configuration module."""

import os
from unittest.mock import patch

from wish_command_generation.config import ClientConfig


def test_default_config():
    """Test default configuration."""
    # Test with no environment variables
    with patch.dict(os.environ, {}, clear=True):
        config = ClientConfig()
        assert config.api_base_url == "http://localhost:3000"
        assert config.generate_endpoint == "http://localhost:3000/generate"


def test_config_from_env():
    """Test loading configuration from environment variables."""
    # Test with custom API URL
    with patch.dict(os.environ, {"WISH_API_BASE_URL": "https://api.example.com"}, clear=True):
        config = ClientConfig.from_env()
        assert config.api_base_url == "https://api.example.com"
        assert config.generate_endpoint == "https://api.example.com/generate"


def test_generate_endpoint_property():
    """Test the generate_endpoint property."""
    # Test with trailing slash
    config = ClientConfig(api_base_url="https://api.example.com/")
    assert config.generate_endpoint == "https://api.example.com/generate"

    # Test without trailing slash
    config = ClientConfig(api_base_url="https://api.example.com")
    assert config.generate_endpoint == "https://api.example.com/generate"

    # Test with custom path
    config = ClientConfig(api_base_url="https://api.example.com/v1")
    assert config.generate_endpoint == "https://api.example.com/v1/generate"

    # Test with custom path and trailing slash
    config = ClientConfig(api_base_url="https://api.example.com/v1/")
    assert config.generate_endpoint == "https://api.example.com/v1/generate"
