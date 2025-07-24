"""Tests for C2 connector factory."""

from unittest.mock import MagicMock, patch

import pytest

from wish_c2 import create_c2_connector, get_c2_connector_from_config
from wish_c2.exceptions import C2Error


class TestFactory:
    """Test C2 connector factory."""

    def test_invalid_c2_type(self):
        """Test invalid C2 type raises error."""
        with pytest.raises(ValueError, match="Unsupported C2 type"):
            create_c2_connector("invalid", mode="real")

    def test_invalid_mode(self):
        """Test invalid mode raises error."""
        with pytest.raises(ValueError, match="Unknown connector mode"):
            create_c2_connector("sliver", mode="invalid")

    def test_real_mode_requires_config_path(self):
        """Test real mode requires config_path."""
        with pytest.raises(ValueError, match="Real mode requires 'config_path'"):
            create_c2_connector("sliver", mode="real")

    def test_safe_mode_requires_config_path(self):
        """Test safe mode requires config_path."""
        with pytest.raises(ValueError, match="Safe mode requires 'config_path'"):
            create_c2_connector("sliver", mode="safe")

    @patch("wish_c2.factory.Path.exists")
    def test_real_mode_config_not_found(self, mock_exists):
        """Test real mode with non-existent config file."""
        mock_exists.return_value = False
        config = {"config_path": "/non/existent/config.cfg"}

        with pytest.raises(C2Error, match="Sliver config file not found"):
            create_c2_connector("sliver", mode="real", config=config)

    @patch("wish_c2.factory.Path.exists")
    @patch("wish_c2.sliver.connector.RealSliverConnector")
    def test_create_real_connector(self, mock_real_class, mock_exists):
        """Test creating real connector."""
        mock_exists.return_value = True
        mock_instance = MagicMock()
        mock_real_class.return_value = mock_instance

        config = {"config_path": "~/.sliver/config.cfg"}
        connector = create_c2_connector("sliver", mode="real", config=config)

        assert connector == mock_instance
        mock_real_class.assert_called_once()

    @patch("wish_c2.factory.Path.exists")
    @patch("wish_c2.sliver.safety.SafeSliverConnector")
    def test_create_safe_connector(self, mock_safe_class, mock_exists):
        """Test creating safe connector."""
        mock_exists.return_value = True
        mock_instance = MagicMock()
        mock_safe_class.return_value = mock_instance

        config = {"config_path": "~/.sliver/config.cfg"}
        connector = create_c2_connector("sliver", mode="safe", config=config)

        assert connector == mock_instance
        mock_safe_class.assert_called_once()


class TestGetConnectorFromConfig:
    """Test getting connector from configuration."""

    def test_c2_disabled(self):
        """Test when C2 is disabled."""
        config = {"c2": {"sliver": {"enabled": False}}}

        with pytest.raises(C2Error, match="Sliver C2 is not enabled"):
            get_c2_connector_from_config(config)

    @patch("wish_c2.factory.Path.exists")
    @patch("wish_c2.sliver.connector.RealSliverConnector")
    def test_default_real_mode(self, mock_real_class, mock_exists):
        """Test default real mode when no mode specified."""
        mock_exists.return_value = True
        mock_instance = MagicMock()
        mock_real_class.return_value = mock_instance

        config = {"c2": {"sliver": {"enabled": True, "config_path": "~/.sliver/config.cfg"}}}

        connector = get_c2_connector_from_config(config)
        assert connector == mock_instance

    @patch("wish_c2.factory.Path.exists")
    @patch("wish_c2.sliver.connector.RealSliverConnector")
    def test_real_mode_from_config(self, mock_real_class, mock_exists):
        """Test real mode from configuration."""
        mock_exists.return_value = True
        mock_instance = MagicMock()
        mock_real_class.return_value = mock_instance

        config = {"c2": {"sliver": {"enabled": True, "mode": "real", "config_path": "~/.sliver/config.cfg"}}}

        connector = get_c2_connector_from_config(config)
        assert connector == mock_instance

    @patch("wish_c2.factory.Path.exists")
    @patch("wish_c2.sliver.safety.SafeSliverConnector")
    def test_safety_config_passed(self, mock_safe_class, mock_exists):
        """Test safety configuration is passed correctly."""
        mock_exists.return_value = True
        mock_instance = MagicMock()
        mock_safe_class.return_value = mock_instance

        config = {
            "c2": {
                "sliver": {
                    "enabled": True,
                    "mode": "safe",
                    "config_path": "~/.sliver/config.cfg",
                    "safety": {"sandbox_mode": True, "allowed_commands": ["ls", "pwd"]},
                }
            }
        }

        connector = get_c2_connector_from_config(config)
        assert connector == mock_instance
        mock_safe_class.assert_called_once()
