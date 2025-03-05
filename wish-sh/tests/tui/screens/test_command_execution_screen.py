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


class TestCommandExecutionScreen:
    """Test for CommandExecutionScreen."""

    @pytest.fixture
    def screen_setup(self):
        """Create a CommandExecutionScreen instance with mocked UI."""
        screen, status_widget, execution_text = CommandExecutionScreenFactory.create_with_mocked_ui(
            wish_manager=WishManagerFactory.create_with_simple_mocks()
        )
        return screen, status_widget, execution_text

    def test_on_mount_executes_commands(self, screen_setup):
        """Test that on_mount executes commands.
        
        This test verifies:
        1. The on_mount method executes all commands in the commands list
        2. Each command is executed with the correct parameters
        3. asyncio.create_task is called to monitor commands
        """
        screen, status_widget, execution_text = screen_setup
        wish_manager = screen.wish_manager
        
        # Call on_mount directly (not as async)
        screen.on_mount()
        
        # Check that execute_command was called for each command
        assert wish_manager.execute_command.call_count == len(screen.commands)
        for i, cmd in enumerate(screen.commands, 1):
            wish_manager.execute_command.assert_any_call(screen.wish, cmd, i)
        
        # Check that asyncio.create_task was called
        asyncio.create_task.assert_called_once()
        
        # Check that monitor_commands was passed to create_task
        args, kwargs = asyncio.create_task.call_args
        assert args[0] == screen.monitor_commands()

    def test_check_all_commands_completed_not_all_done(self, screen_setup):
        """Test check_all_commands_completed when not all commands are done.
        
        This test verifies:
        1. The all_completed flag remains False when commands are still running
        2. The wish state is not updated when commands are still running
        3. The wish is not saved to history when commands are still running
        """
        screen, status_widget, execution_text = screen_setup
        wish = screen.wish
        wish_manager = screen.wish_manager
        
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
        wish_manager.save_wish.assert_not_called()

    def test_check_all_commands_completed_all_success(self, screen_setup):
        """Test check_all_commands_completed when all commands succeed.
        
        This test verifies:
        1. The all_completed flag is set to True when all commands complete
        2. The wish state is updated to DONE when all commands succeed
        3. The wish finished_at timestamp is set
        4. The wish is saved to history
        5. The UI is updated with a completion message
        """
        screen, status_widget, execution_text = screen_setup
        wish = screen.wish
        wish_manager = screen.wish_manager
        
        # Add command results that are all SUCCESS
        for i, cmd in enumerate(screen.commands, 1):
            # Create a mock command result
            result = MagicMock()
            result.state = CommandState.SUCCESS
            result.num = i
            wish.command_results.append(result)
        
        # Mock the tracker.is_all_completed method to return (True, False)
        screen.tracker.is_all_completed = MagicMock(return_value=(True, False))
        
        # Call check_all_commands_completed
        screen.check_all_commands_completed()
        
        # Check that all_completed is True
        assert screen.all_completed
        
        # Check that wish state was updated to DONE
        assert wish.state == WishState.DONE
        assert wish.finished_at is not None
        
        # Check that save_wish was called
        wish_manager.save_wish.assert_called_once_with(wish)
        
        # Check that execution_text was updated
        execution_text.update.assert_any_call("All commands completed.")

    def test_check_all_commands_completed_some_failed(self, screen_setup):
        """Test check_all_commands_completed when some commands fail.
        
        This test verifies:
        1. The all_completed flag is set to True when all commands complete
        2. The wish state is updated to FAILED when any command fails
        3. The wish finished_at timestamp is set
        4. The wish is saved to history
        5. The UI is updated with a failure message
        """
        screen, status_widget, execution_text = screen_setup
        wish = screen.wish
        wish_manager = screen.wish_manager
        
        # Add command results with one FAILED
        result1 = MagicMock()
        result1.state = CommandState.SUCCESS
        result1.num = 1
        wish.command_results.append(result1)
        
        result2 = MagicMock()
        result2.state = CommandState.OTHERS
        result2.num = 2
        wish.command_results.append(result2)
        
        # Mock the tracker.is_all_completed method to return (True, True)
        screen.tracker.is_all_completed = MagicMock(return_value=(True, True))
        
        # Call check_all_commands_completed
        screen.check_all_commands_completed()
        
        # Check that all_completed is True
        assert screen.all_completed
        
        # Check that wish state was updated to FAILED
        assert wish.state == WishState.FAILED
        assert wish.finished_at is not None
        
        # Check that save_wish was called
        wish_manager.save_wish.assert_called_once_with(wish)
        
        # Check that execution_text was updated
        execution_text.update.assert_any_call("All commands completed. Some commands failed.")
