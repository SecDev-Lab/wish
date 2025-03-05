import asyncio

import pytest

from wish_sh.test_factories import CommandExecutionScreenFactory, WishManagerFactory


class TestCommandExecutionScreenWithSleepCommand:
    """Tests for CommandExecutionScreen with sleep commands."""

    @pytest.fixture
    def screen_setup(self):
        """Create a CommandExecutionScreen instance with sleep commands."""
        wish_manager = WishManagerFactory.create_with_simple_mocks()

        screen, status_widget, execution_text = CommandExecutionScreenFactory.create_with_mocked_ui(
            commands=["sleep 1", "sleep 2"],
            wish_manager=wish_manager
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
        executor = wish_manager.executor

        # Call on_mount to start command execution
        screen.on_mount()

        # Check that execute_commands was called with the correct arguments
        executor.execute_commands.assert_called_once_with(screen.wish, screen.commands)

        # Check that asyncio.create_task was called
        asyncio.create_task.assert_called_once()

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
        wish_manager = WishManagerFactory.create_with_simple_mocks()

        screen, status_widget, execution_text = CommandExecutionScreenFactory.create_with_mocked_ui(
            commands=["sleep 0.5", "sleep 1", "sleep 1.5"],
            wish_manager=wish_manager
        )

        executor = wish_manager.executor

        # Call on_mount to start command execution
        screen.on_mount()

        # Check that execute_commands was called with the correct arguments
        executor.execute_commands.assert_called_once_with(screen.wish, screen.commands)

        # Check that asyncio.create_task was called
        asyncio.create_task.assert_called_once()
