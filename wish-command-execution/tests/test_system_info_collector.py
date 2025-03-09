"""Tests for the SystemInfoCollector class."""

import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from wish_models.system_info import SystemInfo

from wish_command_execution.system_info import SystemInfoCollector


class TestSystemInfoCollector(unittest.TestCase):
    """Test cases for the SystemInfoCollector class."""

    def test_collect_system_info_sync(self):
        """Test the collect_system_info_sync method."""
        # Create a mock backend
        mock_backend = MagicMock()

        # Set up the mock to return a SystemInfo object when get_system_info is called
        expected_info = SystemInfo(
            os="TestOS",
            arch="TestArch",
            version="1.0",
            hostname="TestHost",
            username="TestUser"
        )

        # Configure the mock's get_system_info method
        async def mock_get_system_info(*args, **kwargs):
            return expected_info

        mock_backend.get_system_info = mock_get_system_info

        # Create a mock event loop
        mock_loop = MagicMock()
        mock_loop.run_until_complete = MagicMock(return_value=expected_info)

        # Patch asyncio.get_event_loop to return our mock loop
        with patch('asyncio.get_event_loop', return_value=mock_loop):
            # Call the method under test
            result = SystemInfoCollector.collect_system_info_sync(mock_backend)

            # Verify the result
            self.assertEqual(result, expected_info)

            # Verify that run_until_complete was called
            mock_loop.run_until_complete.assert_called_once()


class TestSystemInfoCollectorAsync(unittest.IsolatedAsyncioTestCase):
    """Async test cases for the SystemInfoCollector class."""

    async def test_collect_system_info(self):
        """Test the collect_system_info method."""
        # Create a mock backend
        mock_backend = MagicMock()

        # Set up the mock to return a SystemInfo object when get_system_info is called
        expected_info = SystemInfo(
            os="TestOS",
            arch="TestArch",
            version="1.0",
            hostname="TestHost",
            username="TestUser"
        )

        # Configure the mock's get_system_info method
        mock_backend.get_system_info = AsyncMock(return_value=expected_info)

        # Create the collector
        collector = SystemInfoCollector(mock_backend)

        # Call the method under test
        result = await collector.collect_system_info()

        # Verify the result
        self.assertEqual(result, expected_info)

        # Verify that get_system_info was called
        mock_backend.get_system_info.assert_called_once()

    async def test_collect_system_info_error_handling(self):
        """Test error handling in the collect_system_info method."""
        # Create a mock backend
        mock_backend = MagicMock()

        # Configure the mock's get_system_info method to raise an exception
        mock_backend.get_system_info = AsyncMock(side_effect=Exception("Test error"))

        # Create the collector
        collector = SystemInfoCollector(mock_backend)

        # Call the method under test
        result = await collector.collect_system_info()

        # Verify the result is a minimal SystemInfo object
        self.assertEqual(result.os, "Unknown (Error)")
        self.assertEqual(result.arch, "Unknown")
        self.assertEqual(result.hostname, "Unknown")
        self.assertEqual(result.username, "Unknown")
        self.assertEqual(result.version, "Error: Test error")

        # Verify that get_system_info was called
        mock_backend.get_system_info.assert_called_once()

    async def test_create_minimal_system_info(self):
        """Test the _create_minimal_system_info method."""
        # Call the method under test
        result = SystemInfoCollector._create_minimal_system_info("Test error")

        # Verify the result
        self.assertEqual(result.os, "Unknown (Error)")
        self.assertEqual(result.arch, "Unknown")
        self.assertEqual(result.hostname, "Unknown")
        self.assertEqual(result.username, "Unknown")
        self.assertEqual(result.version, "Error: Test error")

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
        self.assertEqual(result.os, "TestOS")
        self.assertEqual(result.arch, "TestArch")
        self.assertEqual(result.version, "1.0")
        self.assertEqual(result.hostname, "TestHost")
        self.assertEqual(result.username, "TestUser")
        self.assertEqual(result.uid, "1000")
        self.assertEqual(result.gid, "1000")
        self.assertEqual(result.pid, 12345)


if __name__ == '__main__':
    unittest.main()
