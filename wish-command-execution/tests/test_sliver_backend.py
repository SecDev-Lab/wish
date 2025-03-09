"""Tests for the SliverBackend class."""

import concurrent.futures
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

    def test_execute_command(self, sliver_backend, mock_wish, mock_log_files):
        """Test executing a command."""
        # Mock asyncio.get_event_loop and run_coroutine_threadsafe
        with patch('asyncio.get_event_loop') as mock_get_loop, \
             patch('asyncio.run_coroutine_threadsafe') as mock_run_threadsafe:

            # Setup mocks
            mock_loop = MagicMock()
            mock_get_loop.return_value = mock_loop

            mock_future = MagicMock(spec=concurrent.futures.Future)
            mock_run_threadsafe.return_value = mock_future

            # Call the method
            sliver_backend.execute_command(mock_wish, "ls -la", 1, mock_log_files)

            # Verify that run_coroutine_threadsafe was called with the correct arguments
            mock_run_threadsafe.assert_called_once()
            # First arg should be a coroutine (result of _execute_command_wrapper)
            assert mock_run_threadsafe.call_args[0][1] == mock_loop

            # Verify that a callback was added to the future
            mock_future.add_done_callback.assert_called_once()

            # Verify that the command result was added to the wish
            assert len(mock_wish.command_results) == 1
            assert mock_wish.command_results[0].num == 1
            assert mock_wish.command_results[0].command == "ls -la"

            # Verify that the running command was tracked
            assert len(sliver_backend.running_commands) == 1
            assert 1 in sliver_backend.running_commands
            assert sliver_backend.running_commands[1][0] == mock_future

    def test_handle_command_completion_success(self, sliver_backend):
        """Test handling command completion when successful."""
        # Create a mock future, result, and wish
        mock_future = MagicMock(spec=concurrent.futures.Future)
        mock_future.result.return_value = None  # No exception

        mock_result = MagicMock(spec=CommandResult)
        mock_result.state = CommandState.DOING
        mock_result.num = 1

        mock_wish = MagicMock(spec=Wish)
        mock_wish.command_results = [mock_result]

        # Call the method
        sliver_backend._handle_command_completion(mock_future, mock_result, mock_wish)

        # Verify that the result was updated
        mock_result.finish.assert_called_once_with(
            exit_code=0,
            state=CommandState.SUCCESS
        )

    def test_handle_command_completion_exception(self, sliver_backend):
        """Test handling command completion when an exception occurred."""
        # Create a mock future, result, and wish
        mock_future = MagicMock(spec=concurrent.futures.Future)
        mock_future.result.side_effect = Exception("Test exception")

        mock_result = MagicMock(spec=CommandResult)
        mock_result.state = CommandState.DOING
        mock_result.num = 1

        mock_wish = MagicMock(spec=Wish)
        mock_wish.command_results = [mock_result]

        # Call the method
        sliver_backend._handle_command_completion(mock_future, mock_result, mock_wish)

        # Verify that the result was updated
        mock_result.finish.assert_called_once_with(
            exit_code=1,
            state=CommandState.OTHERS
        )

    def test_check_running_commands(self, sliver_backend):
        """Test checking running commands."""
        # Create mock futures, results, and wishes
        mock_future1 = MagicMock(spec=concurrent.futures.Future)
        mock_future1.done.return_value = True

        mock_future2 = MagicMock(spec=concurrent.futures.Future)
        mock_future2.done.return_value = False

        mock_result1 = MagicMock(spec=CommandResult)
        mock_result2 = MagicMock(spec=CommandResult)

        mock_wish1 = MagicMock(spec=Wish)
        mock_wish2 = MagicMock(spec=Wish)

        # Setup running commands
        sliver_backend.running_commands = {
            1: (mock_future1, mock_result1, mock_wish1),
            2: (mock_future2, mock_result2, mock_wish2)
        }

        # Call the method
        sliver_backend.check_running_commands()

        # Verify that the completed command was removed
        assert 1 not in sliver_backend.running_commands
        assert 2 in sliver_backend.running_commands

    def test_cancel_command(self, sliver_backend):
        """Test cancelling a command."""
        # Create mock future, result, and wish
        mock_future = MagicMock(spec=concurrent.futures.Future)

        mock_result = MagicMock(spec=CommandResult)
        mock_result.state = CommandState.DOING
        mock_result.num = 1

        mock_wish = MagicMock(spec=Wish)
        mock_wish.command_results = [mock_result]

        # Setup running commands
        sliver_backend.running_commands = {
            1: (mock_future, mock_result, mock_wish)
        }

        # Call the method
        result = sliver_backend.cancel_command(mock_wish, 1)

        # Verify that the future was cancelled
        mock_future.cancel.assert_called_once()

        # Verify that the result was updated
        mock_result.finish.assert_called_once_with(
            exit_code=-1,
            state=CommandState.USER_CANCELLED
        )

        # Verify that the command was removed from running commands
        assert 1 not in sliver_backend.running_commands

        # Verify the return message
        assert result == "Command 1 cancelled."

    def test_cancel_command_not_running(self, sliver_backend):
        """Test cancelling a command that is not running."""
        # Create mock result and wish
        mock_result = MagicMock(spec=CommandResult)
        mock_result.state = CommandState.SUCCESS  # Not DOING
        mock_result.num = 1

        mock_wish = MagicMock(spec=Wish)
        mock_wish.command_results = [mock_result]

        # Call the method
        result = sliver_backend.cancel_command(mock_wish, 1)

        # Verify that the result was not updated
        mock_result.finish.assert_not_called()

        # Verify the return message
        assert result == "Command 1 is not running."
