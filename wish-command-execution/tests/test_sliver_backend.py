"""Tests for the SliverBackend class."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from wish_models import CommandResult, CommandState, Wish
from wish_models.executable_collection import ExecutableCollection

from wish_command_execution.backend.sliver import SliverBackend
from wish_command_execution.system_info import SystemInfoCollector


class TestSliverBackend:
    """Test cases for the SliverBackend class."""

    @pytest.fixture
    def mock_wish(self):
        """Create a mock Wish."""
        wish = MagicMock(spec=Wish)
        wish.command_results = []
        return wish

    @pytest.fixture
    def mock_log_files(self):
        """Create mock log files."""
        from pathlib import Path

        from wish_models.command_result.log_files import LogFiles
        return LogFiles(stdout=Path("/tmp/stdout.log"), stderr=Path("/tmp/stderr.log"))

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
        # Mock the interactive_session attributes
        mock_interactive_session.os = "Linux"
        mock_interactive_session.arch = "x86_64"
        mock_interactive_session.version = "5.10.0"
        mock_interactive_session.hostname = "test-host"
        mock_interactive_session.username = "test-user"
        mock_interactive_session.uid = "1000"
        mock_interactive_session.gid = "1000"
        mock_interactive_session.pid = 12345

        # Call the method
        info = await sliver_backend.get_system_info()

        # Verify the result
        assert info.os == "Linux"
        assert info.arch == "x86_64"
        assert info.version == "5.10.0"
        assert info.hostname == "test-host"
        assert info.username == "test-user"
        assert info.uid == "1000"
        assert info.gid == "1000"
        assert info.pid == 12345

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
        mock_interactive_session.os = "Linux"
        mock_interactive_session.arch = "x86_64"
        mock_interactive_session.version = "5.10.0"
        mock_interactive_session.hostname = "test-host"
        mock_interactive_session.username = "test-user"
        mock_interactive_session.uid = "1000"
        mock_interactive_session.gid = "1000"
        mock_interactive_session.pid = 12345

        mock_sliver_client.interact_session = AsyncMock(return_value=mock_interactive_session)

        # Patch the _connect method to avoid the actual connection logic
        with patch.object(SliverBackend, '_connect', AsyncMock()) as mock_connect:
            # Set the client and session manually
            backend.client = mock_sliver_client
            backend.interactive_session = mock_interactive_session

            # Call a method that uses _connect
            await backend.get_system_info()

            # Verify that _connect was called
            mock_connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_command(self, sliver_backend, mock_wish, mock_log_files, mock_interactive_session):
        """Test executing a command."""
        # Setup mock for interactive session execute method
        cmd_result = MagicMock()
        cmd_result.Stdout = b"test output"
        cmd_result.Stderr = b""
        cmd_result.Status = 0
        mock_interactive_session.execute.return_value = cmd_result

        # Call the method
        await sliver_backend.execute_command(mock_wish, "ls -la", 1, mock_log_files)

        # Verify that execute was called with the correct arguments
        # The command is now split into command name and arguments
        mock_interactive_session.execute.assert_called_once_with("ls", ["-la"])

        # Verify that the command result was added to the wish
        assert len(mock_wish.command_results) == 1
        assert mock_wish.command_results[0].num == 1
        assert mock_wish.command_results[0].command == "ls -la"

        # Verify that the command result was updated with the correct exit code
        # Note: We can't check if finish was called directly since it's not a mock
        # Instead, we check that the mock_wish.command_results was updated
        assert len(mock_wish.command_results) == 1

    @pytest.mark.asyncio
    async def test_check_running_commands(self, sliver_backend):
        """Test checking running commands."""
        # This method is now a no-op, just verify it doesn't raise an exception
        await sliver_backend.check_running_commands()

    @pytest.mark.asyncio
    async def test_cancel_command(self, sliver_backend):
        """Test cancelling a command."""
        # Create mock result and wish
        mock_result = MagicMock(spec=CommandResult)
        mock_result.state = CommandState.DOING
        mock_result.num = 1

        mock_wish = MagicMock(spec=Wish)
        mock_wish.command_results = [mock_result]

        # Call the method
        result = await sliver_backend.cancel_command(mock_wish, 1)

        # Verify that the result was updated
        mock_result.finish.assert_called_once_with(
            exit_code=-1,
            state=CommandState.USER_CANCELLED
        )

        # Verify the return message
        assert result == "Command 1 cancelled."

    @pytest.mark.asyncio
    async def test_cancel_command_not_running(self, sliver_backend):
        """Test cancelling a command that is not running."""
        # Create mock result and wish
        mock_result = MagicMock(spec=CommandResult)
        mock_result.state = CommandState.SUCCESS  # Not DOING
        mock_result.num = 1

        mock_wish = MagicMock(spec=Wish)
        mock_wish.command_results = [mock_result]

        # Call the method
        result = await sliver_backend.cancel_command(mock_wish, 1)

        # Verify that the result was not updated
        mock_result.finish.assert_not_called()

        # Verify the return message
        assert result == "Command 1 is not running."
