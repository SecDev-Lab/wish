import asyncio
import pytest
from unittest.mock import MagicMock, patch

from textual.app import App
from textual.widgets import Static

from wish_models import CommandState, Wish, WishState, UtcDatetime
from wish_sh.settings import Settings
from wish_sh.wish_manager import WishManager
from wish_sh.wish_tui import CommandExecutionScreen


class TestCommandExecutionScreenWithSleepCommand:
    """Test CommandExecutionScreen with sleep commands."""

    @pytest.fixture
    def wish(self):
        """Create a test wish."""
        wish = Wish.create("Test sleep command")
        wish.state = WishState.DOING
        return wish

    @pytest.fixture
    def commands(self):
        """Create test commands with sleep."""
        return ["sleep 1", "sleep 2"]

    @pytest.fixture
    def wish_manager(self):
        """Create a mock WishManager."""
        manager = MagicMock(spec=WishManager)
        
        # Add running_commands attribute explicitly
        manager.running_commands = {}
        
        # Make execute_command actually execute the command
        def execute_command_side_effect(wish, command, cmd_num):
            import subprocess
            from pathlib import Path
            
            # Create a simple log files structure
            log_files = MagicMock()
            log_files.stdout = Path(f"/tmp/stdout_{cmd_num}.log")
            log_files.stderr = Path(f"/tmp/stderr_{cmd_num}.log")
            
            # Create a command result
            result = MagicMock()
            result.command = command
            result.state = CommandState.DOING
            result.num = cmd_num
            result.log_files = log_files
            result.exit_code = None
            result.finished_at = None
            
            # Add the result to the wish
            wish.command_results.append(result)
            
            # Start the process
            process = subprocess.Popen(command, shell=True)
            
            # Store in running commands dict
            manager.running_commands[cmd_num] = (process, result, wish)
            
            return result
            
        manager.execute_command.side_effect = execute_command_side_effect
        
        # Make check_running_commands actually check the commands
        def check_running_commands_side_effect():
            for cmd_num, (process, result, wish) in list(manager.running_commands.items()):
                if process.poll() is not None:  # Process has finished
                    # Update the result
                    result.state = CommandState.SUCCESS if process.returncode == 0 else CommandState.OTHERS
                    result.exit_code = process.returncode
                    result.finished_at = UtcDatetime.now()
                    
                    # Remove from running commands
                    del manager.running_commands[cmd_num]
                    
        manager.check_running_commands.side_effect = check_running_commands_side_effect
        
        return manager

    @pytest.fixture
    def screen(self, wish, commands, wish_manager):
        """Create a CommandExecutionScreen instance."""
        return CommandExecutionScreen(wish, commands, wish_manager)

    @pytest.mark.asyncio
    async def test_sleep_command_execution_and_ui_update(self, screen, wish_manager):
        """Test that sleep commands are executed and the UI is updated correctly.
        
        TODO Remove this test (for debugging)
        """
        # Mock the set_interval method to avoid timer issues in tests
        screen.set_interval = MagicMock()
        
        # Mock the query_one method to return a mock Static widget
        status_widget = MagicMock(spec=Static)
        execution_text = MagicMock(spec=Static)
        
        def query_one_side_effect(selector):
            if selector == "#execution-text":
                return execution_text
            else:
                return status_widget
                
        screen.query_one = MagicMock(side_effect=query_one_side_effect)
        
        # Call on_mount to start command execution
        screen.on_mount()
        
        # Check that execute_command was called for each command
        assert wish_manager.execute_command.call_count == len(screen.commands)
        
        # Check that set_interval was called to set up the timer
        screen.set_interval.assert_called_once()
        
        # Manually call update_command_status to simulate the timer
        screen.update_command_status()
        
        # Check that check_running_commands was called
        wish_manager.check_running_commands.assert_called_once()
        
        # Check that the UI was updated
        status_widget.update.assert_called()
        
        # Wait for the first command to complete
        await asyncio.sleep(1.1)
        
        # Reset the mock to check new calls
        wish_manager.check_running_commands.reset_mock()
        status_widget.update.reset_mock()
        
        # Call update_command_status again
        screen.update_command_status()
        
        # Check that check_running_commands was called again
        wish_manager.check_running_commands.assert_called_once()
        
        # Check that the UI was updated again
        status_widget.update.assert_called()
        
        # Wait for the second command to complete
        await asyncio.sleep(1.1)
        
        # Reset the mock to check new calls
        wish_manager.check_running_commands.reset_mock()
        status_widget.update.reset_mock()
        execution_text.update.reset_mock()
        
        # Call update_command_status again
        screen.update_command_status()
        
        # Check that check_running_commands was called again
        wish_manager.check_running_commands.assert_called_once()
        
        # Check that the UI was updated again
        status_widget.update.assert_called()
        
        # Check that all commands have completed
        assert len(wish_manager.running_commands) == 0
        
        # Check that the execution text was updated to show completion
        execution_text.update.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_sleep_command_with_different_durations(self, wish, wish_manager):
        """Test that sleep commands with different durations are executed and tracked correctly.
        
        TODO Remove this test (for debugging)
        """
        # Create commands with different sleep durations
        commands = ["sleep 0.5", "sleep 1", "sleep 1.5"]
        
        # Create a screen with these commands
        screen = CommandExecutionScreen(wish, commands, wish_manager)
        
        # Mock the set_interval method to avoid timer issues in tests
        screen.set_interval = MagicMock()
        
        # Mock the query_one method to return a mock Static widget
        status_widget = MagicMock(spec=Static)
        execution_text = MagicMock(spec=Static)
        
        def query_one_side_effect(selector):
            if selector == "#execution-text":
                return execution_text
            else:
                return status_widget
                
        screen.query_one = MagicMock(side_effect=query_one_side_effect)
        
        # Call on_mount to start command execution
        screen.on_mount()
        
        # Check that execute_command was called for each command
        assert wish_manager.execute_command.call_count == len(commands)
        
        # Wait for the first command to complete
        await asyncio.sleep(0.6)
        
        # Call update_command_status
        screen.update_command_status()
        
        # Check that the first command has completed
        assert 1 not in wish_manager.running_commands
        
        # Wait for the second command to complete
        await asyncio.sleep(0.5)
        
        # Call update_command_status again
        screen.update_command_status()
        
        # Check that the second command has completed
        assert 2 not in wish_manager.running_commands
        
        # Wait for the third command to complete
        await asyncio.sleep(0.5)
        
        # Call update_command_status again
        screen.update_command_status()
        
        # Check that all commands have completed
        assert len(wish_manager.running_commands) == 0
        
        # Check that the execution text was updated to show completion
        execution_text.update.assert_called()
