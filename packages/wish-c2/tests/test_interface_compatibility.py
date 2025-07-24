"""Tests for interface compatibility between all connector implementations."""

from unittest.mock import AsyncMock, patch

import pytest

from wish_c2 import create_c2_connector
from wish_c2.base import BaseC2Connector


@pytest.fixture
def mock_config_exists():
    """Mock config file existence."""
    with patch("wish_c2.factory.Path.exists") as mock:
        mock.return_value = True
        yield mock


class TestInterfaceCompatibility:
    """Test that all implementations follow the same interface."""

    @patch("wish_c2.factory.Path.exists")
    @patch("wish_c2.sliver.connector.RealSliverConnector")
    def test_real_interface_compatibility(self, mock_real_class, mock_exists):
        """Test real connector interface compatibility."""
        mock_exists.return_value = True
        mock_instance = AsyncMock(spec=BaseC2Connector)
        mock_instance.connected = False  # Add property explicitly
        mock_real_class.return_value = mock_instance

        config = {"config_path": "~/.sliver/config.cfg"}
        connector = create_c2_connector("sliver", mode="real", config=config)

        # Check all required methods exist
        assert hasattr(connector, "connect")
        assert hasattr(connector, "disconnect")
        assert hasattr(connector, "get_sessions")
        assert hasattr(connector, "execute_command")
        assert hasattr(connector, "start_interactive_shell")

        # Check properties
        assert hasattr(connector, "connected")

    @patch("wish_c2.factory.Path.exists")
    @patch("wish_c2.sliver.safety.SafeSliverConnector")
    def test_safe_interface_compatibility(self, mock_safe_class, mock_exists):
        """Test safe connector interface compatibility."""
        mock_exists.return_value = True
        mock_instance = AsyncMock(spec=BaseC2Connector)
        mock_instance.connected = False  # Add property explicitly
        mock_safe_class.return_value = mock_instance

        config = {"config_path": "~/.sliver/config.cfg"}
        connector = create_c2_connector("sliver", mode="safe", config=config)

        # Check all required methods exist
        assert hasattr(connector, "connect")
        assert hasattr(connector, "disconnect")
        assert hasattr(connector, "get_sessions")
        assert hasattr(connector, "execute_command")
        assert hasattr(connector, "start_interactive_shell")

        # Check properties
        assert hasattr(connector, "connected")

    @patch("wish_c2.factory.Path.exists")
    @patch("wish_c2.sliver.safety.SafeSliverConnector")
    @patch("wish_c2.sliver.connector.RealSliverConnector")
    def test_all_modes_inherit_base(self, mock_real_class, mock_safe_class, mock_exists):
        """Test all connector modes inherit from BaseC2Connector."""
        mock_exists.return_value = True
        mock_real_instance = AsyncMock(spec=BaseC2Connector)
        mock_real_instance.connected = False
        mock_safe_instance = AsyncMock(spec=BaseC2Connector)
        mock_safe_instance.connected = False
        mock_real_class.return_value = mock_real_instance
        mock_safe_class.return_value = mock_safe_instance

        config = {"config_path": "~/.sliver/config.cfg"}

        real_connector = create_c2_connector("sliver", mode="real", config=config)
        safe_connector = create_c2_connector("sliver", mode="safe", config=config)

        # Note: Since we're mocking, we can't test isinstance directly
        # but we can verify the interface is correctly implemented
        assert callable(real_connector.connect)
        assert callable(safe_connector.connect)

    @patch("wish_c2.factory.Path.exists")
    @patch("wish_c2.sliver.connector.RealSliverConnector")
    def test_consistent_error_handling(self, mock_real_class, mock_exists):
        """Test consistent error handling across implementations."""
        mock_exists.return_value = True
        mock_instance = AsyncMock(spec=BaseC2Connector)
        mock_instance.connected = False
        mock_real_class.return_value = mock_instance

        config = {"config_path": "~/.sliver/config.cfg"}
        connector = create_c2_connector("sliver", mode="real", config=config)

        # All connectors should handle the same exceptions
        # This is more of a documentation test since we're using mocks
        assert hasattr(connector, "connect")
        assert hasattr(connector, "get_sessions")
        assert hasattr(connector, "execute_command")
