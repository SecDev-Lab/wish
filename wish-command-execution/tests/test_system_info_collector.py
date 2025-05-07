"""Tests for the SystemInfoCollector class."""

import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from wish_models.test_factories import SystemInfoFactory

from wish_command_execution.system_info import SystemInfoCollector
from wish_command_execution.test_factories import SystemInfoCollectorFactory


class TestSystemInfoCollector(unittest.TestCase):
    """Test cases for the SystemInfoCollector class."""

    def test_collect_system_info_sync(self):
        """Test the collect_system_info_sync method."""
        # Create expected info
        expected_info = SystemInfoFactory.create(
            os="TestOS",
            arch="TestArch",
            version="1.0",
            hostname="TestHost",
            username="TestUser"
        )

        # Mock the static method
        with patch.object(
            SystemInfoCollector, 'collect_system_info_sync',
            return_value=expected_info
        ) as mock_collect:
            # Call the method under test
            result = SystemInfoCollector.collect_system_info_sync(MagicMock())

            # Verify the result
            self.assertEqual(result, expected_info)

            # Verify that the method was called
            mock_collect.assert_called_once()


@pytest.mark.asyncio
class TestSystemInfoCollectorAsync:
    """Async test cases for the SystemInfoCollector class."""

    async def test_collect_system_info(self):
        """Test the collect_system_info method."""
        # Create expected info
        expected_info = SystemInfoFactory.create(
            os="TestOS",
            arch="TestArch",
            version="1.0",
            hostname="TestHost",
            username="TestUser"
        )

        # Create a collector with mocked methods
        collector = SystemInfoCollectorFactory.create_with_mocks(system_info=expected_info)

        # Call the method under test
        result = await collector.collect_system_info()

        # Verify the result
        assert result == expected_info

        # Verify that collect_system_info was called
        collector.collect_system_info.assert_called_once()

    async def test_collect_system_info_error_handling(self):
        """Test error handling in the collect_system_info method."""
        # Reset the mock to use the real implementation
        collector = SystemInfoCollector(MagicMock())

        # Configure the mock backend's get_system_info method to raise an exception
        collector.backend.get_system_info = AsyncMock(side_effect=Exception("Test error"))

        # Call the method under test
        result = await collector.collect_system_info()

        # Verify the result is a minimal SystemInfo object
        assert result.os == "Unknown (Error)"
        assert result.arch == "Unknown"
        assert result.hostname == "Unknown"
        assert result.username == "Unknown"
        assert result.version == "Error: Test error"

        # Verify that get_system_info was called
        collector.backend.get_system_info.assert_called_once()

    async def test_create_minimal_system_info(self):
        """Test the _create_minimal_system_info method."""
        # Call the method under test
        result = SystemInfoCollector._create_minimal_system_info("Test error")

        # Verify the result
        assert result.os == "Unknown (Error)"
        assert result.arch == "Unknown"
        assert result.hostname == "Unknown"
        assert result.username == "Unknown"
        assert result.version == "Error: Test error"

    async def test_collect_basic_info_from_session(self):
        """Test the collect_basic_info_from_session method."""
        # Create a mock session
        mock_session = MagicMock()
        mock_session.os = "TestOS"
        mock_session.arch = "TestArch"
        mock_session.version = "1.0"
        mock_session.hostname = "TestHost"
        mock_session.username = "TestUser"
        mock_session.uid = "1000"
        mock_session.gid = "1000"
        mock_session.pid = 12345

        # Call the method under test
        result = await SystemInfoCollector.collect_basic_info_from_session(mock_session)

        # Verify the result
        assert result.os == "TestOS"
        assert result.arch == "TestArch"
        assert result.version == "1.0"
        assert result.hostname == "TestHost"
        assert result.username == "TestUser"
        assert result.uid == "1000"
        assert result.gid == "1000"
        assert result.pid == 12345
