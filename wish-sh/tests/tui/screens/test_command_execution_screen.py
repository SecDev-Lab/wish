import asyncio
import pytest
from unittest.mock import MagicMock, patch

from textual.app import App
from textual.widgets import Static

from wish_models import CommandState, Wish, WishState, UtcDatetime
from wish_sh.settings import Settings
from wish_sh.wish_manager import WishManager
from wish_sh.wish_tui import CommandExecutionScreen


class TestCommandExecutionScreen:
    """Test for CommandExecutionScreen."""

    @pytest.fixture
    def wish(self):
        """Create a test wish."""
        wish = Wish.create("Test wish")
        wish.state = WishState.DOING
        return wish

    @pytest.fixture
    def commands(self):
        """Create test commands."""
        return ["echo 'Test command 1'", "echo 'Test command 2'"]

    @pytest.fixture
    def wish_manager(self):
        """Create a mock WishManager."""
        manager = MagicMock(spec=WishManager)
        manager.execute_command = MagicMock()
        manager.check_running_commands = MagicMock()
        manager.save_wish = MagicMock()
        return manager

    @pytest.fixture
    def screen(self, wish, commands, wish_manager):
        """Create a CommandExecutionScreen instance."""
        return CommandExecutionScreen(wish, commands, wish_manager)

    def test_on_mount_executes_commands(self, screen, wish_manager, commands):
        """Test that on_mount executes commands."""
        # TODO Remove this test (for debugging)
        # Mock the set_interval method to avoid timer issues in tests
        screen.set_interval = MagicMock()
        
        # Call on_mount directly (not as async)
        screen.on_mount()
        
        # Check that execute_command was called for each command
        assert wish_manager.execute_command.call_count == len(commands)
        for i, cmd in enumerate(commands, 1):
            wish_manager.execute_command.assert_any_call(screen.wish, cmd, i)
        
        # Check that set_interval was called to set up the timer
        screen.set_interval.assert_called_once()

    def test_update_command_status(self, screen, wish_manager):
        """Test that update_command_status updates the command status."""
        # TODO Remove this test (for debugging)
        # Mock methods
        screen.update_ui = MagicMock()
        screen.check_all_commands_completed = MagicMock()
        
        # Call update_command_status
        screen.update_command_status()
        
        # Check that methods were called
        wish_manager.check_running_commands.assert_called_once()
        screen.update_ui.assert_called_once()
        screen.check_all_commands_completed.assert_called_once()

    def test_update_ui(self, screen, wish):
        """Test that update_ui updates the UI with command statuses."""
        # TODO Remove this test (for debugging)
        # Create mock Static widgets for command statuses
        status_widget = MagicMock(spec=Static)
        screen.query_one = MagicMock(return_value=status_widget)
        
        # Add command results to the wish
        for i, cmd in enumerate(screen.commands, 1):
            result = MagicMock()
            result.state = CommandState.SUCCESS
            result.exit_code = 0
            result.log_summary = f"Test summary {i}"
            result.num = i
            wish.command_results.append(result)
        
        # Call update_ui
        screen.update_ui()
        
        # Check that query_one was called for each command
        assert screen.query_one.call_count == len(screen.commands)
        
        # Check that update was called on the widget
        assert status_widget.update.call_count == len(screen.commands)

    def test_check_all_commands_completed_not_all_done(self, screen, wish):
        """Test check_all_commands_completed when not all commands are done."""
        # TODO Remove this test (for debugging)
        # Add a command result that is still DOING
        result = MagicMock()
        result.state = CommandState.DOING
        result.num = 1
        wish.command_results.append(result)
        
        # Call check_all_commands_completed
        screen.check_all_commands_completed()
        
        # Check that all_completed is still False
        assert not screen.all_completed
        
        # Check that wish state was not updated
        assert wish.state == WishState.DOING
        assert wish.finished_at is None
        
        # Check that save_wish was not called
        screen.wish_manager.save_wish.assert_not_called()

    def test_check_all_commands_completed_all_success(self, screen, wish):
        """Test check_all_commands_completed when all commands succeed."""
        # TODO Remove this test (for debugging)
        # Mock the query_one method
        execution_text = MagicMock(spec=Static)
        screen.query_one = MagicMock(return_value=execution_text)
        
        # Add command results that are all SUCCESS
        for i, cmd in enumerate(screen.commands, 1):
            result = MagicMock()
            result.state = CommandState.SUCCESS
            result.num = i
            wish.command_results.append(result)
        
        # Call check_all_commands_completed
        screen.check_all_commands_completed()
        
        # Check that all_completed is True
        assert screen.all_completed
        
        # Check that wish state was updated to DONE
        assert wish.state == WishState.DONE
        assert wish.finished_at is not None
        
        # Check that save_wish was called
        screen.wish_manager.save_wish.assert_called_once_with(wish)
        
        # Check that execution_text was updated
        execution_text.update.assert_called_once_with("All commands completed.")

    def test_check_all_commands_completed_some_failed(self, screen, wish):
        """Test check_all_commands_completed when some commands fail."""
        # TODO Remove this test (for debugging)
        # Mock the query_one method
        execution_text = MagicMock(spec=Static)
        screen.query_one = MagicMock(return_value=execution_text)
        
        # Add command results with one FAILED
        result1 = MagicMock()
        result1.state = CommandState.SUCCESS
        result1.num = 1
        wish.command_results.append(result1)
        
        result2 = MagicMock()
        result2.state = CommandState.OTHERS
        result2.num = 2
        wish.command_results.append(result2)
        
        # Call check_all_commands_completed
        screen.check_all_commands_completed()
        
        # Check that all_completed is True
        assert screen.all_completed
        
        # Check that wish state was updated to FAILED
        assert wish.state == WishState.FAILED
        assert wish.finished_at is not None
        
        # Check that save_wish was called
        screen.wish_manager.save_wish.assert_called_once_with(wish)
        
        # Check that execution_text was updated
        execution_text.update.assert_called_once_with("All commands completed. Some commands failed.")
