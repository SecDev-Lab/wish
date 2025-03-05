"""Tests for CommandExecutor."""

import pytest
from unittest.mock import MagicMock

from wish_models import Wish
from wish_models.test_factories import WishDoingFactory
from wish_sh.command_execution import CommandExecutor
from wish_sh.test_factories import WishManagerFactory


class TestCommandExecutor:
    """Tests for CommandExecutor."""

    @pytest.fixture
    def wish_manager(self):
        """Create a mock WishManager."""
        return WishManagerFactory.create_with_simple_mocks()

    @pytest.fixture
    def wish(self):
        """Create a test wish."""
        wish = WishDoingFactory.create()
        wish.command_results = []  # Clear any existing command results
        return wish

    @pytest.fixture
    def executor(self, wish_manager):
        """Create a CommandExecutor instance."""
        return CommandExecutor(wish_manager)

    def test_execute_command(self, executor, wish_manager, wish):
        """Test execute_command method.
        
        This test verifies that the execute_command method correctly delegates
        to the WishManager's execute_command method.
        """
        # Execute a command
        cmd = "echo 'Test command'"
        cmd_num = 1
        executor.execute_command(wish, cmd, cmd_num)
        
        # Verify that WishManager.execute_command was called with the correct arguments
        wish_manager.execute_command.assert_called_once_with(wish, cmd, cmd_num)

    def test_execute_commands(self, executor, wish_manager, wish):
        """Test execute_commands method.
        
        This test verifies that the execute_commands method correctly executes
        multiple commands.
        """
        # Execute multiple commands
        commands = ["echo 'Command 1'", "echo 'Command 2'", "echo 'Command 3'"]
        executor.execute_commands(wish, commands)
        
        # Verify that WishManager.execute_command was called for each command
        assert wish_manager.execute_command.call_count == len(commands)
        
        # Verify that each command was executed with the correct arguments
        for i, cmd in enumerate(commands, 1):
            wish_manager.execute_command.assert_any_call(wish, cmd, i)

    def test_cancel_command(self, executor, wish_manager, wish):
        """Test cancel_command method.
        
        This test verifies that the cancel_command method correctly delegates
        to the WishManager's cancel_command method.
        """
        # Set up the mock to return a specific message
        expected_message = "Command 1 cancelled."
        wish_manager.cancel_command.return_value = expected_message
        
        # Cancel a command
        cmd_num = 1
        result = executor.cancel_command(wish, cmd_num)
        
        # Verify that WishManager.cancel_command was called with the correct arguments
        wish_manager.cancel_command.assert_called_once_with(wish, cmd_num)
        
        # Verify that the correct message was returned
        assert result == expected_message
