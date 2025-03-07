"""Tests for BashBackend."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from wish_models import CommandState, LogFiles
from wish_models.test_factories import WishDoingFactory

from wish_command_execution.backend import BashBackend


class TestBashBackend:
    """Tests for BashBackend."""

    @pytest.fixture
    def backend(self):
        """Create a BashBackend instance."""
        return BashBackend()

    @pytest.fixture
    def wish(self):
        """Create a test wish."""
        wish = WishDoingFactory.create()
        wish.command_results = []  # Clear any existing command results
        return wish

    @pytest.fixture
    def log_files(self):
        """Create test log files."""
        return LogFiles(
            stdout=Path("/mock/log/dir/1.stdout"),
            stderr=Path("/mock/log/dir/1.stderr")
        )

    @patch("subprocess.Popen")
    @patch("builtins.open")
    def test_execute_command(self, mock_open, mock_popen, backend, wish, log_files):
        """Test execute_command method.

        This test verifies that the execute_command method correctly executes
        a command and creates the necessary log files.
        """
        # Set up the mock Popen
        mock_process = MagicMock()
        mock_popen.return_value = mock_process

        # Set up mock file objects
        mock_stdout = MagicMock()
        mock_stderr = MagicMock()
        mock_open.return_value.__enter__.side_effect = [mock_stdout, mock_stderr]

        # Execute a command
        cmd = "echo 'Test command'"
        cmd_num = 1
        backend.execute_command(wish, cmd, cmd_num, log_files)

        # Verify that Popen was called
        mock_popen.assert_called_once()

        # Verify that the command result was added to the wish
        assert len(wish.command_results) == 1
        assert wish.command_results[0].command == cmd
        assert wish.command_results[0].num == cmd_num

        # Verify that the command was added to running_commands
        assert cmd_num in backend.running_commands
        assert backend.running_commands[cmd_num][0] == mock_process

    @patch("subprocess.Popen")
    @patch("builtins.open")
    def test_execute_command_subprocess_error(self, mock_open, mock_popen, backend, wish, log_files):
        """Test execute_command method with subprocess error.

        This test verifies that the execute_command method correctly handles
        subprocess errors.
        """
        # Set up the mock Popen to raise a subprocess error
        mock_popen.side_effect = subprocess.SubprocessError("Mock error")

        # Set up mock file objects
        mock_stdout = MagicMock()
        mock_stderr = MagicMock()
        mock_open.return_value.__enter__.side_effect = [mock_stdout, mock_stderr]

        # Execute a command
        cmd = "echo 'Test command'"
        cmd_num = 1
        backend.execute_command(wish, cmd, cmd_num, log_files)

        # Verify that the command result was updated with the error state
        assert wish.command_results[0].state == CommandState.OTHERS

        # Verify that the command result was added to the wish
        assert len(wish.command_results) == 1
        assert wish.command_results[0].command == cmd
        assert wish.command_results[0].num == cmd_num

        # Verify that the command result was updated
        assert wish.command_results[0].state == CommandState.OTHERS
        assert wish.command_results[0].exit_code == 1

    def test_check_running_commands(self, backend, wish):
        """Test check_running_commands method.

        This test verifies that the check_running_commands method correctly
        updates the status of running commands.
        """
        # Create mock process, result, and wish
        mock_process = MagicMock()
        mock_process.poll.return_value = 0  # Process has completed successfully

        mock_result = MagicMock()
        mock_result.finish = MagicMock()

        # Add to running_commands
        cmd_num = 1
        backend.running_commands[cmd_num] = (mock_process, mock_result, wish)

        # Check running commands
        backend.check_running_commands()

        # Verify that poll was called
        mock_process.poll.assert_called_once()

        # Verify that finish was called
        mock_result.finish.assert_called_once()

        # Verify that the command was processed
        assert mock_result.finish.called

        # Verify that the command was removed from running_commands
        assert cmd_num not in backend.running_commands

    def test_cancel_command(self, backend, wish):
        """Test cancel_command method.

        This test verifies that the cancel_command method correctly cancels
        a running command.
        """
        # Create mock process, result, and wish
        mock_process = MagicMock()
        mock_process.terminate = MagicMock()
        mock_process.kill = MagicMock()
        mock_process.poll.return_value = None  # Process is still running

        mock_result = MagicMock()
        mock_result.finish = MagicMock()

        # Add to running_commands
        cmd_num = 1
        backend.running_commands[cmd_num] = (mock_process, mock_result, wish)

        # Cancel the command
        result = backend.cancel_command(wish, cmd_num)

        # Verify that terminate was called
        mock_process.terminate.assert_called_once()

        # Verify that finish was called
        mock_result.finish.assert_called_once()

        # Verify that the command was processed
        assert mock_result.finish.called

        # Verify that the command was removed from running_commands
        assert cmd_num not in backend.running_commands

        # Verify that the correct message was returned
        assert result == f"Command {cmd_num} cancelled."

    def test_cancel_command_not_running(self, backend, wish):
        """Test cancel_command method when command is not running.

        This test verifies that the cancel_command method correctly handles
        the case where the command is not running.
        """
        # Cancel a command that is not running
        cmd_num = 1
        result = backend.cancel_command(wish, cmd_num)

        # Verify that the correct message was returned
        assert result == f"Command {cmd_num} is not running."
