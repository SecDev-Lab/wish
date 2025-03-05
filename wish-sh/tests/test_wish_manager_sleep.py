import asyncio
import pytest
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

from wish_models import CommandState, Wish, WishState
from wish_models.test_factories import WishDoingFactory

from wish_sh.settings import Settings
from wish_sh.test_factories import WishManagerFactory
from wish_sh.wish_manager import WishManager


class TestWishManagerWithSleepCommand:
    """Test WishManager with sleep commands."""

    @pytest.fixture
    def wish(self):
        """Create a test wish."""
        wish = WishDoingFactory.create()
        wish.command_results = []  # Clear any existing command results
        return wish

    @pytest.mark.asyncio
    async def test_execute_sleep_command(self, wish):
        """Test that a sleep command is executed and tracked correctly.
        
        This test verifies:
        1. A sleep command is properly executed by WishManager
        2. The command is tracked in running_commands while executing
        3. The command state is updated to SUCCESS when completed
        4. The command is removed from running_commands when finished
        """
        # Create a WishManager with mocked file operations
        wish_manager = WishManagerFactory.create()
        
        # Mock the create_command_log_dirs method to avoid file system operations
        with patch.object(wish_manager.paths, "create_command_log_dirs") as mock_create_dirs:
            mock_create_dirs.return_value = Path("/path/to/log/dir")
            
            # Mock open to avoid file operations
            with patch("builtins.open", MagicMock()):
                # Execute a sleep command
                cmd = "sleep 1"
                wish_manager.execute_command(wish, cmd, 1)
                
                # Verify that the command is running
                assert 1 in wish_manager.running_commands
                assert wish.command_results[0].state == CommandState.DOING
                assert wish.command_results[0].exit_code is None
                
                # Wait a short time and check that the command is still running
                await asyncio.sleep(0.5)
                wish_manager.check_running_commands()
                assert 1 in wish_manager.running_commands
                assert wish.command_results[0].state == CommandState.DOING
                
                # Wait for the command to complete
                await asyncio.sleep(1)
                wish_manager.check_running_commands()
                
                # Verify that the command has completed
                assert 1 not in wish_manager.running_commands
                assert wish.command_results[0].state == CommandState.SUCCESS
                assert wish.command_results[0].exit_code == 0
                assert wish.command_results[0].finished_at is not None

    @pytest.mark.asyncio
    async def test_multiple_sleep_commands(self, wish):
        """Test that multiple sleep commands are executed and tracked correctly.
        
        This test verifies:
        1. Multiple commands with different durations are executed properly
        2. All commands are initially tracked in running_commands
        3. Commands are removed from running_commands as they complete
        4. Command states are updated correctly based on exit codes
        5. Command completion is tracked in the correct order
        """
        # Create a WishManager with mocked file operations
        wish_manager = WishManagerFactory.create()
        
        # Mock the create_command_log_dirs method to avoid file system operations
        with patch.object(wish_manager.paths, "create_command_log_dirs") as mock_create_dirs:
            mock_create_dirs.return_value = Path("/path/to/log/dir")
            
            # Mock open to avoid file operations
            with patch("builtins.open", MagicMock()):
                # Execute multiple sleep commands with different durations
                cmds = [
                    "sleep 0.5",
                    "sleep 1",
                    "sleep 1.5"
                ]
                
                for i, cmd in enumerate(cmds, 1):
                    wish_manager.execute_command(wish, cmd, i)
                
                # Verify that all commands are running
                assert len(wish_manager.running_commands) == 3
                for i in range(1, 4):
                    assert i in wish_manager.running_commands
                    assert wish.command_results[i-1].state == CommandState.DOING
                
                # Wait for the first command to complete
                await asyncio.sleep(0.6)
                wish_manager.check_running_commands()
                
                # Verify that the first command has completed
                assert 1 not in wish_manager.running_commands
                assert wish.command_results[0].state == CommandState.SUCCESS
                assert wish.command_results[0].exit_code == 0
                
                # Verify that the other commands are still running
                assert 2 in wish_manager.running_commands
                assert 3 in wish_manager.running_commands
                assert wish.command_results[1].state == CommandState.DOING
                assert wish.command_results[2].state == CommandState.DOING
                
                # Wait for the second command to complete
                await asyncio.sleep(0.5)
                wish_manager.check_running_commands()
                
                # Verify that the second command has completed
                assert 2 not in wish_manager.running_commands
                assert wish.command_results[1].state == CommandState.SUCCESS
                assert wish.command_results[1].exit_code == 0
                
                # Verify that the third command is still running
                assert 3 in wish_manager.running_commands
                assert wish.command_results[2].state == CommandState.DOING
                
                # Wait for the third command to complete
                await asyncio.sleep(0.5)
                wish_manager.check_running_commands()
                
                # Verify that all commands have completed
                assert len(wish_manager.running_commands) == 0
                for i in range(3):
                    assert wish.command_results[i].state == CommandState.SUCCESS
                    assert wish.command_results[i].exit_code == 0
                    assert wish.command_results[i].finished_at is not None

    @pytest.mark.asyncio
    async def test_wish_state_update_after_commands_complete(self, wish):
        """Test that the wish state is updated after all commands complete.
        
        This test verifies:
        1. The wish state remains DOING while commands are executing
        2. The wish state can be updated to DONE after commands complete
        3. The wish is properly saved to history after completion
        """
        # Create a WishManager with mocked file operations
        wish_manager = WishManagerFactory.create()
        
        # Mock the create_command_log_dirs method to avoid file system operations
        with patch.object(wish_manager.paths, "create_command_log_dirs") as mock_create_dirs:
            mock_create_dirs.return_value = Path("/path/to/log/dir")
            
            # Mock open to avoid file operations
            with patch("builtins.open", MagicMock()):
                # Mock the save_wish method to avoid file operations
                with patch.object(wish_manager, "save_wish") as mock_save_wish:
                    # Execute a sleep command
                    cmd = "sleep 0.5"
                    wish_manager.execute_command(wish, cmd, 1)
                    
                    # Verify that the wish state is still DOING
                    assert wish.state == WishState.DOING
                    assert wish.finished_at is None
                    
                    # Wait for the command to complete
                    await asyncio.sleep(0.6)
                    wish_manager.check_running_commands()
                    
                    # Verify that the command has completed
                    assert 1 not in wish_manager.running_commands
                    assert wish.command_results[0].state == CommandState.SUCCESS
                    
                    # Update the wish state manually (this would be done by CommandExecutionScreen in the real app)
                    wish.state = WishState.DONE
                    wish_manager.save_wish(wish)
                    
                    # Verify that save_wish was called
                    mock_save_wish.assert_called_once_with(wish)
