"""Tests for CommandExecutor."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from wish_models.test_factories import WishDoingFactory

from wish_command_execution import CommandExecutor
from wish_command_execution.backend import Backend


class MockBackend(Backend):
    """Mock implementation of Backend for testing."""

    def __init__(self):
        self.execute_command = MagicMock()
        self.check_running_commands = MagicMock()
        self.cancel_command = MagicMock(return_value="Command cancelled")


class TestCommandExecutor:
    """Tests for CommandExecutor."""

    @pytest.fixture
    def backend(self):
        """Create a mock backend."""
        return MockBackend()

    @pytest.fixture
    def log_dir_creator(self):
        """Create a mock log directory creator."""
        return MagicMock(return_value=Path("/mock/log/dir"))

    @pytest.fixture
    def wish(self):
        """Create a test wish."""
        wish = WishDoingFactory.create()
        wish.command_results = []  # Clear any existing command results
        return wish

    @pytest.fixture
    def executor(self, backend, log_dir_creator):
        """Create a CommandExecutor instance."""
        return CommandExecutor(backend=backend, log_dir_creator=log_dir_creator)

    def test_execute_command(self, executor, backend, log_dir_creator, wish):
        """Test execute_command method.

        This test verifies that the execute_command method correctly delegates
        to the backend's execute_command method.
        """
        # Execute a command
        cmd = "echo 'Test command'"
        cmd_num = 1
        executor.execute_command(wish, cmd, cmd_num)

        # Verify that log_dir_creator was called
        log_dir_creator.assert_called_once_with(wish.id)

        # Verify that backend.execute_command was called with the correct arguments
        backend.execute_command.assert_called_once()
        args, _ = backend.execute_command.call_args
        assert args[0] == wish
        assert args[1] == cmd
        assert args[2] == cmd_num
        assert str(args[3].stdout) == "/mock/log/dir/1.stdout"
        assert str(args[3].stderr) == "/mock/log/dir/1.stderr"

    def test_execute_commands(self, executor, wish):
        """Test execute_commands method.

        This test verifies that the execute_commands method correctly executes
        multiple commands.
        """
        # Mock the execute_command method
        executor.execute_command = MagicMock()

        # Execute multiple commands
        commands = ["echo 'Command 1'", "echo 'Command 2'", "echo 'Command 3'"]
        executor.execute_commands(wish, commands)

        # Verify that execute_command was called for each command
        assert executor.execute_command.call_count == len(commands)

        # Verify that each command was executed with the correct arguments
        for i, cmd in enumerate(commands, 1):
            executor.execute_command.assert_any_call(wish, cmd, i)

    def test_check_running_commands(self, executor, backend):
        """Test check_running_commands method.

        This test verifies that the check_running_commands method correctly delegates
        to the backend's check_running_commands method.
        """
        # Check running commands
        executor.check_running_commands()

        # Verify that backend.check_running_commands was called
        backend.check_running_commands.assert_called_once()

    def test_cancel_command(self, executor, backend, wish):
        """Test cancel_command method.

        This test verifies that the cancel_command method correctly delegates
        to the backend's cancel_command method.
        """
        # Cancel a command
        cmd_num = 1
        result = executor.cancel_command(wish, cmd_num)

        # Verify that backend.cancel_command was called with the correct arguments
        backend.cancel_command.assert_called_once_with(wish, cmd_num)

        # Verify that the correct message was returned
        assert result == "Command cancelled"

    def test_default_log_dir_creator(self, backend):
        """Test _default_log_dir_creator method.

        This test verifies that the _default_log_dir_creator method correctly
        creates a log directory.
        """
        # Create an executor with the default log_dir_creator
        executor = CommandExecutor(backend=backend)

        # Create a temporary directory for testing
        with patch("pathlib.Path.mkdir") as mock_mkdir:
            # Call the default log_dir_creator
            log_dir = executor._default_log_dir_creator("test-wish-id")

            # Verify that the correct directory was created
            assert str(log_dir) == "logs/test-wish-id/commands"
            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
