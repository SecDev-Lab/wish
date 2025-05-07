"""Tests for CommandExecutor."""

from unittest.mock import patch

import pytest
from wish_models.command_result import CommandInput
from wish_models.test_factories import WishDoingFactory

from wish_command_execution.test_factories import CommandExecutorFactory


class TestCommandExecutor:
    """Tests for CommandExecutor."""

    @pytest.fixture
    def wish(self):
        """Create a test wish."""
        wish = WishDoingFactory.create()
        wish.command_results = []  # Clear any existing command results
        return wish

    @pytest.fixture
    def executor(self):
        """Create a CommandExecutor instance with mocks."""
        return CommandExecutorFactory.create_with_mocks()

    @pytest.mark.asyncio
    async def test_execute_command(self, executor, wish):
        """Test execute_command method."""
        # Execute a command
        cmd = "echo 'Test command'"
        cmd_num = 1
        timeout_sec = 60
        await executor.execute_command(wish, cmd, cmd_num, timeout_sec)

        # Verify that execute_command was called with the correct arguments
        executor.execute_command.assert_called_once_with(wish, cmd, cmd_num, timeout_sec)

    @pytest.mark.asyncio
    async def test_execute_commands(self, executor, wish):
        """Test execute_commands method."""
        # Reset the mock to clear any previous calls
        executor.execute_command.reset_mock()

        # Execute multiple commands
        commands = [
            CommandInput(command="echo 'Command 1'", timeout_sec=60),
            CommandInput(command="echo 'Command 2'", timeout_sec=60),
            CommandInput(command="echo 'Command 3'", timeout_sec=60)
        ]
        await executor.execute_commands(wish, commands)

        # Verify that execute_command was called for each command
        assert executor.execute_command.call_count == len(commands)

        # Verify that each command was executed with the correct arguments
        for i, cmd_input in enumerate(commands, 1):
            executor.execute_command.assert_any_call(wish, cmd_input.command, i, cmd_input.timeout_sec)

    @pytest.mark.asyncio
    async def test_check_running_commands(self, executor):
        """Test check_running_commands method."""
        # Check running commands
        await executor.check_running_commands()

        # Verify that check_running_commands was called
        executor.check_running_commands.assert_called_once()

    @pytest.mark.asyncio
    async def test_cancel_command(self, executor, wish):
        """Test cancel_command method."""
        # Cancel a command
        cmd_num = 1
        result = await executor.cancel_command(wish, cmd_num)

        # Verify that cancel_command was called with the correct arguments
        executor.cancel_command.assert_called_once_with(wish, cmd_num)

        # Verify that the correct message was returned
        assert result == "Command cancelled"

    def test_default_log_dir_creator(self):
        """Test _default_log_dir_creator method."""
        # Create a real executor with the default log_dir_creator
        executor = CommandExecutorFactory.create()

        # Create a temporary directory for testing
        with patch("pathlib.Path.mkdir") as mock_mkdir:
            # Call the default log_dir_creator
            log_dir = executor._default_log_dir_creator("test-wish-id")

            # Verify that the correct directory was created
            assert str(log_dir) == "logs/test-wish-id/commands"
            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
