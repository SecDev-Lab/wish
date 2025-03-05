import asyncio
import pytest
from unittest.mock import MagicMock, patch

from textual.app import App
from textual.widgets import Static

from wish_models import CommandState, Wish, WishState, UtcDatetime
from wish_models.test_factories import WishDoingFactory
from wish_sh.settings import Settings
from wish_sh.test_factories import CommandExecutionScreenFactory, WishManagerFactory
from wish_sh.wish_manager import WishManager
from wish_sh.wish_tui import CommandExecutionScreen


class TestCommandExecutionScreenWithSleepCommand:
    """Test CommandExecutionScreen with sleep commands."""

    @pytest.fixture
    def screen_setup(self):
        """Create a CommandExecutionScreen instance with mocked UI."""
        screen, status_widget, execution_text = CommandExecutionScreenFactory.create_with_mocked_ui(
            commands=["sleep 1", "sleep 2"],
            wish_manager=WishManagerFactory.create_with_mock_execute()
        )
        return screen, status_widget, execution_text

    @pytest.mark.asyncio
    async def test_sleep_command_execution_and_ui_update(self, screen_setup):
        """Test that sleep commands are executed and the UI is updated correctly.
        
        This test verifies:
        1. Commands are properly executed when the screen is mounted
        2. The UI is updated as commands progress
        3. The execution status is correctly tracked
        4. The completion message is displayed when all commands finish
        """
        screen, status_widget, execution_text = screen_setup
        wish_manager = screen.wish_manager
        
        # Call on_mount to start command execution
        screen.on_mount()
        
        # Check that execute_command was called for each command
        assert wish_manager.execute_command.call_count == len(screen.commands)
        
        # Check that asyncio.create_task was called
        asyncio.create_task.assert_called_once()
        
        # Manually call the tracker and ui_updater to simulate the monitor_commands method
        screen.tracker.check_status(screen.wish)
        screen.ui_updater.update_command_status(screen.wish)
        
        # Check that check_running_commands was called
        wish_manager.check_running_commands.assert_called_once()
        
        # Check that the UI was updated
        status_widget.update.assert_called()
        
        # Wait for the first command to complete
        await asyncio.sleep(1.1)
        
        # Reset the mock to check new calls
        wish_manager.check_running_commands.reset_mock()
        status_widget.update.reset_mock()
        
        # Manually call the tracker and ui_updater again
        screen.tracker.check_status(screen.wish)
        screen.ui_updater.update_command_status(screen.wish)
        
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
        
        # Manually call the tracker and ui_updater again
        screen.tracker.check_status(screen.wish)
        screen.ui_updater.update_command_status(screen.wish)
        
        # Check that check_running_commands was called again
        wish_manager.check_running_commands.assert_called_once()
        
        # Check that the UI was updated again
        status_widget.update.assert_called()
        
        # Check that all commands have completed
        assert len(wish_manager.running_commands) == 0
        
        # Mock the tracker.is_all_completed method to return (True, False)
        screen.tracker.is_all_completed = MagicMock(return_value=(True, False))
        
        # Manually call check_all_commands_completed to simulate the monitor_commands method
        screen.check_all_commands_completed()
        
        # Check that the execution text was updated to show completion
        execution_text.update.assert_called()
        
    @pytest.mark.asyncio
    async def test_sleep_command_with_different_durations(self):
        """Test that sleep commands with different durations are executed and tracked correctly.
        
        This test verifies:
        1. Multiple commands with different durations are executed properly
        2. Each command's completion is tracked independently
        3. The running_commands dictionary is updated correctly as commands complete
        4. All commands eventually complete and the final status is updated
        """
        # Create a screen with commands of different durations
        screen, status_widget, execution_text = CommandExecutionScreenFactory.create_with_mocked_ui(
            commands=["sleep 0.5", "sleep 1", "sleep 1.5"],
            wish_manager=WishManagerFactory.create_with_mock_execute()
        )
        
        wish_manager = screen.wish_manager
        
        # Call on_mount to start command execution
        screen.on_mount()
        
        # Check that execute_command was called for each command
        assert wish_manager.execute_command.call_count == len(screen.commands)
        
        # Wait for the first command to complete
        await asyncio.sleep(0.6)
        
        # Manually call the tracker to check status
        screen.tracker.check_status(screen.wish)
        
        # Check that the first command has completed
        assert 1 not in wish_manager.running_commands
        
        # Wait for the second command to complete
        await asyncio.sleep(0.5)
        
        # Manually call the tracker to check status again
        screen.tracker.check_status(screen.wish)
        
        # Check that the second command has completed
        assert 2 not in wish_manager.running_commands
        
        # Wait for the third command to complete
        await asyncio.sleep(0.5)
        
        # Manually call the tracker to check status again
        screen.tracker.check_status(screen.wish)
        
        # Check that all commands have completed
        assert len(wish_manager.running_commands) == 0
        
        # Mock the tracker.is_all_completed method to return (True, False)
        screen.tracker.is_all_completed = MagicMock(return_value=(True, False))
        
        # Manually call check_all_commands_completed to simulate the monitor_commands method
        screen.check_all_commands_completed()
        
        # Check that the execution text was updated to show completion
        execution_text.update.assert_called()
