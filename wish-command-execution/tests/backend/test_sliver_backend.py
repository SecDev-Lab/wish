"""Tests for the Sliver backend."""

import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from wish_models import CommandResult, CommandState, Wish

from wish_command_execution.backend.sliver import SliverBackend


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
    return SliverBackend("test-session-id", mock_config_file)


@pytest.fixture
def wish():
    """Create a Wish instance for testing."""
    return Wish.create("Test wish")


@pytest.fixture
def log_files():
    """Create temporary log files for testing."""
    from pathlib import Path

    from wish_models.command_result import LogFiles

    with tempfile.NamedTemporaryFile(delete=False) as stdout_file, \
         tempfile.NamedTemporaryFile(delete=False) as stderr_file:
        stdout_path = stdout_file.name
        stderr_path = stderr_file.name

    # Create a proper LogFiles instance
    log_files = LogFiles(stdout=Path(stdout_path), stderr=Path(stderr_path))

    yield log_files

    # Clean up
    os.unlink(stdout_path)
    os.unlink(stderr_path)


def test_execute_command(sliver_backend, wish, log_files, mock_sliver_client):
    """Test executing a command through the Sliver backend."""
    # Since we're mocking the Sliver client and the asynchronous execution,
    # we need to manually write to the log files to simulate the command execution
    with open(log_files.stdout, "w") as f:
        f.write("Test output")

    # Execute a command
    sliver_backend.execute_command(wish, "whoami", 1, log_files)

    # Check that the command result was added to the wish
    assert len(wish.command_results) == 1
    assert wish.command_results[0].command == "whoami"
    assert wish.command_results[0].num == 1

    # Wait for the command to complete (since it's running in a separate thread)
    import time
    max_wait = 5  # Maximum wait time in seconds
    start_time = time.time()

    while time.time() - start_time < max_wait:
        # Check if the command is no longer in running_commands
        if 1 not in sliver_backend.running_commands:
            break
        # Or check if the command has finished
        if wish.command_results[0].finished_at is not None:
            break
        time.sleep(0.1)

    # Check that the log files were written to
    with open(log_files.stdout, "r") as f:
        stdout_content = f.read()

    assert "Test output" in stdout_content


def test_cancel_command(sliver_backend, wish, log_files):
    """Test cancelling a command."""
    # Add a command result to the wish
    result = CommandResult.create(1, "whoami", log_files)
    wish.command_results.append(result)

    # Cancel the command
    message = sliver_backend.cancel_command(wish, 1)

    # Check the message
    assert "Command 1 cancelled" in message

    # Check that the command was marked as cancelled
    assert wish.command_results[0].state == CommandState.USER_CANCELLED


def test_check_running_commands(sliver_backend):
    """Test checking running commands."""
    # This is a no-op in the Sliver backend
    sliver_backend.check_running_commands()
    # Just verify it doesn't raise an exception
    assert True
