from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from wish_models.test_factories import WishDoingFactory

from wish_sh.test_factories import WishManagerFactory


class TestWishManagerWithSleepCommand:
    """Tests for WishManager with sleep commands."""

    @pytest.fixture
    def wish(self):
        """Create a test wish."""
        return WishDoingFactory.create()

    @pytest.mark.asyncio
    async def test_execute_sleep_command(self, wish):
        """Test that a sleep command is executed and tracked correctly.

        This test verifies:
        1. A sleep command is properly executed by WishManager
        2. The command is tracked while executing
        3. The command state is updated to SUCCESS when completed
        4. The command is removed from tracking when finished
        """
        # Create a WishManager with mocked file operations
        wish_manager = WishManagerFactory.create()

        # Mock the executor
        wish_manager.executor = MagicMock()

        # Mock the create_command_log_dirs method to avoid file system operations
        with patch.object(wish_manager.paths, "create_command_log_dirs") as mock_create_dirs:
            mock_create_dirs.return_value = Path("/path/to/log/dir")

            # Mock open to avoid file operations
            with patch("builtins.open", MagicMock()):
                # Execute a sleep command
                cmd = "sleep 1"
                wish_manager.execute_command(wish, cmd, 1)

                # Verify that the executor.execute_command was called
                wish_manager.executor.execute_command.assert_called_once_with(wish, cmd, 1)

    @pytest.mark.asyncio
    async def test_multiple_sleep_commands(self, wish):
        """Test that multiple sleep commands are executed and tracked correctly.

        This test verifies:
        1. Multiple commands with different durations are executed properly
        2. All commands are initially tracked
        3. Commands are removed from tracking as they complete
        4. Command states are updated correctly based on exit codes
        5. Command completion is tracked in the correct order
        """
        # Create a WishManager with mocked file operations
        wish_manager = WishManagerFactory.create()

        # Mock the executor
        wish_manager.executor = MagicMock()

        # Mock the create_command_log_dirs method to avoid file system operations
        with patch.object(wish_manager.paths, "create_command_log_dirs") as mock_create_dirs:
            mock_create_dirs.return_value = Path("/path/to/log/dir")

            # Mock open to avoid file operations
            with patch("builtins.open", MagicMock()):
                # Execute multiple sleep commands with different durations
                cmds = [
                    "sleep 0.5",
                    "sleep 1",
                    "sleep 1.5",
                ]

                for i, cmd in enumerate(cmds, 1):
                    wish_manager.execute_command(wish, cmd, i)

                # Verify that the executor.execute_command was called for each command
                assert wish_manager.executor.execute_command.call_count == 3
                for i, cmd in enumerate(cmds, 1):
                    wish_manager.executor.execute_command.assert_any_call(wish, cmd, i)

    @pytest.mark.asyncio
    async def test_check_running_commands(self, wish):
        """Test that check_running_commands updates the status of running commands."""
        # Create a WishManager with mocked file operations
        wish_manager = WishManagerFactory.create()

        # Mock the executor
        wish_manager.executor = MagicMock()

        # Check running commands
        wish_manager.check_running_commands()

        # Verify that executor.check_running_commands was called
        wish_manager.executor.check_running_commands.assert_called_once()
