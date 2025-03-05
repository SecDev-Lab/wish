"""Tests for CommandExecutor."""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from wish_models import Wish, CommandResult, LogFiles
from wish_models.test_factories import WishDoingFactory
from wish_sh.command_execution import CommandExecutor


class MockWishManager:
    """Mock implementation of WishManager for testing."""
    
    def __init__(self):
        self.create_command_log_dirs = MagicMock(return_value=Path("/mock/log/dir"))
        self.save_wish = MagicMock()
        self.summarize_log = MagicMock(return_value="Mock log summary")


class TestCommandExecutor:
    """Tests for CommandExecutor."""

    @pytest.fixture
    def wish_manager(self):
        """Create a mock WishManager."""
        return MockWishManager()

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

    @patch("subprocess.Popen")
    @patch("builtins.open")
    def test_execute_command(self, mock_open, mock_popen, executor, wish_manager, wish):
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
        mock_open.side_effect = [mock_stdout, mock_stderr]
        
        # Execute a command
        cmd = "echo 'Test command'"
        cmd_num = 1
        executor.execute_command(wish, cmd, cmd_num)
        
        # Verify that create_command_log_dirs was called
        wish_manager.create_command_log_dirs.assert_called_once_with(wish.id)
        
        # Verify that Popen was called with the correct arguments
        mock_popen.assert_called_once()
        
        # Verify that the command result was added to the wish
        assert len(wish.command_results) == 1
        assert wish.command_results[0].command == cmd
        assert wish.command_results[0].num == cmd_num
        
        # Verify that the command was added to running_commands
        assert cmd_num in executor.running_commands
        assert executor.running_commands[cmd_num][0] == mock_process

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

    def test_check_running_commands(self, executor, wish_manager, wish):
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
        executor.running_commands[cmd_num] = (mock_process, mock_result, wish)
        
        # Check running commands
        executor.check_running_commands()
        
        # Verify that poll was called
        mock_process.poll.assert_called_once()
        
        # Verify that finish was called with the correct arguments
        mock_result.finish.assert_called_once()
        
        # Verify that the command was removed from running_commands
        assert cmd_num not in executor.running_commands

    def test_cancel_command(self, executor, wish_manager, wish):
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
        executor.running_commands[cmd_num] = (mock_process, mock_result, wish)
        
        # Cancel the command
        result = executor.cancel_command(wish, cmd_num)
        
        # Verify that terminate was called
        mock_process.terminate.assert_called_once()
        
        # Verify that finish was called
        mock_result.finish.assert_called_once()
        
        # Verify that the command was removed from running_commands
        assert cmd_num not in executor.running_commands
        
        # Verify that the correct message was returned
        assert result == f"Command {cmd_num} cancelled."
