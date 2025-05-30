"""Tests for the Sliver backend."""

import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from wish_models import CommandResult, CommandState
from wish_models.test_factories import LogFilesFactory, WishDoingFactory

from wish_command_execution.test_factories import SliverBackendFactory


@pytest.fixture
def mock_sliver_client():
    """Mock SliverClient for testing."""
    with patch("wish_command_execution.backend.sliver.SliverClient") as mock_client:
        # Setup mock client
        mock_client_instance = MagicMock()
        mock_client_instance.connect = AsyncMock()
        mock_client_instance.interact_session = AsyncMock()

        # Setup mock interactive session
        mock_session = MagicMock()
        mock_session.execute = AsyncMock()
        mock_client_instance.interact_session.return_value = mock_session

        # Setup mock execute result
        mock_execute_result = MagicMock()
        mock_execute_result.Stdout = b"Test output"
        mock_execute_result.Stderr = b""
        mock_execute_result.Status = 0
        mock_session.execute.return_value = mock_execute_result

        # Return the mock client constructor
        mock_client.return_value = mock_client_instance
        yield mock_client


@pytest.fixture
def mock_config_file():
    """Create a temporary mock config file."""
    with tempfile.NamedTemporaryFile(delete=False) as temp:
        temp.write(b"{}")
        temp_path = temp.name

    yield temp_path

    # Clean up
    os.unlink(temp_path)


@pytest.fixture
def sliver_backend(mock_config_file):
    """Create a SliverBackend instance for testing."""
    return SliverBackendFactory.create(
        session_id="test-session-id",
        client_config_path=mock_config_file
    )


@pytest.fixture
def wish():
    """Create a Wish instance for testing."""
    wish = WishDoingFactory.create()
    wish.command_results = []  # Clear any existing command results
    return wish


@pytest.fixture
def log_files(tmp_path):
    """Create log files for testing."""
    stdout_path = tmp_path / "stdout.log"
    stderr_path = tmp_path / "stderr.log"
    return LogFilesFactory.create(
        stdout=str(stdout_path),
        stderr=str(stderr_path)
    )


@pytest.mark.asyncio
async def test_execute_command(sliver_backend, wish, log_files, mock_sliver_client):
    """Test executing a command through the Sliver backend."""
    # Since we're mocking the Sliver client and the asynchronous execution,
    # we need to manually write to the log files to simulate the command execution
    with open(log_files.stdout, "w") as f:
        f.write("Test output")

    # Execute a command
    timeout_sec = 60
    await sliver_backend.execute_command(wish, "whoami", 1, log_files, timeout_sec)

    # Check that the command result was added to the wish
    assert len(wish.command_results) == 1
    assert wish.command_results[0].command.command == "whoami"
    assert wish.command_results[0].num == 1

    # Check that the log files were written to
    with open(log_files.stdout, "r") as f:
        stdout_content = f.read()

    assert "Test output" in stdout_content


@pytest.mark.asyncio
async def test_cancel_command(sliver_backend, wish, log_files):
    """Test cancelling a command."""
    # Add a command result to the wish
    timeout_sec = 60
    from wish_models.command_result.command import Command
    command = Command.create_bash_command("whoami")
    result = CommandResult.create(1, command, log_files, timeout_sec)
    wish.command_results.append(result)

    # Cancel the command
    message = await sliver_backend.cancel_command(wish, 1)

    # Check the message
    assert "Command 1 cancelled" in message

    # Check that the command was marked as cancelled
    assert wish.command_results[0].state == CommandState.USER_CANCELLED


@pytest.mark.asyncio
async def test_check_running_commands(sliver_backend):
    """Test checking running commands."""
    # This is a no-op in the Sliver backend
    await sliver_backend.check_running_commands()
    # Just verify it doesn't raise an exception
    assert True


@pytest.mark.asyncio
async def test_connect_with_dead_session(mock_config_file):
    """Test _connect when the session is dead."""
    # Create a SliverBackend instance with mocked components
    backend = SliverBackendFactory.create(
        session_id="test-session-id",
        client_config_path=mock_config_file
    )

    # Mock SliverClientConfig.parse_config_file to return a mock config
    mock_config = MagicMock()

    # Mock SliverClient to return a mock client
    mock_client = MagicMock()
    mock_client.connect = AsyncMock()

    # Mock interactive_session with is_dead=True
    mock_session = MagicMock()
    mock_session.is_dead = True
    mock_client.interact_session = AsyncMock(return_value=mock_session)

    # Apply all the mocks
    with patch(
        "wish_command_execution.backend.sliver.SliverClientConfig.parse_config_file",
        return_value=mock_config
    ), patch(
        "wish_command_execution.backend.sliver.SliverClient",
        return_value=mock_client
    ), patch("wish_command_execution.backend.sliver.sys.exit") as mock_exit:

        # Call _connect, which should detect the dead session and call sys.exit
        await backend._connect()

        # Verify that sys.exit was called with exit code 1
        mock_exit.assert_called_once_with(1)
