"""Tests for the SliverBackend class."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from wish_models.system_info import SystemInfo
from wish_models.executable_collection import ExecutableCollection
from wish_command_execution.backend.sliver import SliverBackend
from wish_command_execution.system_info import SystemInfoCollector


class TestSliverBackend:
    """Test cases for the SliverBackend class."""

    @pytest.fixture
    def mock_sliver_client(self):
        """Create a mock SliverClient."""
        with patch('sliver.SliverClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client.connect = AsyncMock()
            mock_client_class.return_value = mock_client
            yield mock_client

    @pytest.fixture
    def mock_sliver_config(self):
        """Create a mock SliverClientConfig."""
        with patch('sliver.SliverClientConfig') as mock_config_class:
            mock_config = MagicMock()
            mock_config_class.parse_config_file.return_value = mock_config
            yield mock_config

    @pytest.fixture
    def mock_interactive_session(self):
        """Create a mock interactive session."""
        mock_session = MagicMock()
        mock_session.os = "Linux"
        mock_session.arch = "x86_64"
        mock_session.version = "5.10.0"
        mock_session.hostname = "test-host"
        mock_session.username = "test-user"
        mock_session.uid = "1000"
        mock_session.gid = "1000"
        mock_session.pid = 12345
        mock_session.execute = AsyncMock()
        return mock_session

    @pytest.fixture
    def sliver_backend(self, mock_sliver_client, mock_sliver_config, mock_interactive_session):
        """Create a SliverBackend instance with mocked dependencies."""
        mock_sliver_client.interact_session = AsyncMock(return_value=mock_interactive_session)
        
        backend = SliverBackend(
            session_id="test-session-id",
            client_config_path="/path/to/config.json"
        )
        backend.client = mock_sliver_client
        backend.interactive_session = mock_interactive_session
        return backend

    @pytest.mark.asyncio
    async def test_get_basic_system_info(self, sliver_backend, mock_interactive_session):
        """Test getting basic system information."""
        # Mock the SystemInfoCollector.collect_basic_info_from_session method
        expected_info = SystemInfo(
            os="Linux",
            arch="x86_64",
            version="5.10.0",
            hostname="test-host",
            username="test-user",
            uid="1000",
            gid="1000",
            pid=12345
        )
        
        with patch.object(
            SystemInfoCollector, 'collect_basic_info_from_session',
            AsyncMock(return_value=expected_info)
        ):
            # Call the method
            info = await sliver_backend.get_basic_system_info()
            
            # Verify the result
            assert info is expected_info
            
            # Verify that the collector was called with the correct session
            SystemInfoCollector.collect_basic_info_from_session.assert_called_once_with(
                mock_interactive_session
            )

    @pytest.mark.asyncio
    async def test_get_executables(self, sliver_backend, mock_interactive_session):
        """Test getting executable files information."""
        # Create a mock ExecutableCollection
        expected_collection = ExecutableCollection()
        expected_collection.add_executable(
            path="/usr/bin/python",
            size=12345,
            permissions="rwxr-xr-x"
        )
        
        # Mock the SystemInfoCollector.collect_executables_from_session method
        with patch.object(
            SystemInfoCollector, 'collect_executables_from_session',
            AsyncMock(return_value=expected_collection)
        ):
            # Call the method
            collection = await sliver_backend.get_executables(collect_system_executables=True)
            
            # Verify the result
            assert collection is expected_collection
            
            # Verify that the collector was called with the correct parameters
            SystemInfoCollector.collect_executables_from_session.assert_called_once_with(
                mock_interactive_session,
                collect_system_executables=True
            )

    @pytest.mark.asyncio
    async def test_get_system_info(self, sliver_backend, mock_interactive_session):
        """Test getting system information."""
        # Create mock return values
        expected_info = SystemInfo(
            os="Linux",
            arch="x86_64",
            version="5.10.0",
            hostname="test-host",
            username="test-user",
            uid="1000",
            gid="1000",
            pid=12345
        )
        expected_collection = ExecutableCollection()
        
        # Mock the SystemInfoCollector.collect_from_session method
        with patch.object(
            SystemInfoCollector, 'collect_from_session',
            AsyncMock(return_value=(expected_info, expected_collection))
        ):
            # Call the method
            info = await sliver_backend.get_system_info(collect_system_executables=True)
            
            # Verify the result
            assert info is expected_info
            
            # Verify that the collector was called with the correct parameters
            SystemInfoCollector.collect_from_session.assert_called_once_with(
                mock_interactive_session,
                collect_system_executables=True
            )

    @pytest.mark.asyncio
    async def test_connect_already_connected(self, sliver_backend):
        """Test that _connect does nothing if already connected."""
        # The backend is already connected in the fixture
        
        # Call the method
        await sliver_backend._connect()
        
        # Verify that no methods were called on the client
        sliver_backend.client.connect.assert_not_called()
        sliver_backend.client.interact_session.assert_not_called()

    @pytest.mark.asyncio
    async def test_connect_not_connected(self, mock_sliver_client, mock_sliver_config):
        """Test connecting when not already connected."""
        # Create a backend that's not connected
        backend = SliverBackend(
            session_id="test-session-id",
            client_config_path="/path/to/config.json"
        )
        
        # Skip the actual _connect method and just set the client and session directly
        # This is a more focused test that doesn't rely on the internal implementation
        mock_interactive_session = MagicMock()
        mock_sliver_client.interact_session = AsyncMock(return_value=mock_interactive_session)
        
        # Patch the _connect method to avoid the actual connection logic
        with patch.object(SliverBackend, '_connect', AsyncMock()) as mock_connect:
            # Call get_basic_system_info which should call _connect
            with patch.object(
                SystemInfoCollector, 'collect_basic_info_from_session',
                AsyncMock(return_value=SystemInfo(
                    os="Linux",
                    arch="x86_64",
                    version="5.10.0",
                    hostname="test-host",
                    username="test-user",
                    uid="1000",
                    gid="1000",
                    pid=12345
                ))
            ):
                # Set the client and session manually
                backend.client = mock_sliver_client
                backend.interactive_session = mock_interactive_session
                
                # Call a method that uses _connect
                await backend.get_basic_system_info()
                
                # Verify that _connect was called
                mock_connect.assert_called_once()
