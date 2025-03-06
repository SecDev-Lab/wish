"""Tests for CommandStatusTracker."""

from unittest.mock import MagicMock, patch

import pytest
from wish_models import CommandState, UtcDatetime, WishState
from wish_models.test_factories import WishDoingFactory

from wish_command_execution import CommandExecutor, CommandStatusTracker


class TestCommandStatusTracker:
    """Tests for CommandStatusTracker."""

    @pytest.fixture
    def executor(self):
        """Create a mock CommandExecutor."""
        executor = MagicMock(spec=CommandExecutor)
        executor.check_running_commands = MagicMock()
        return executor

    @pytest.fixture
    def wish_saver(self):
        """Create a mock wish saver function."""
        return MagicMock()

    @pytest.fixture
    def wish(self):
        """Create a test wish."""
        wish = WishDoingFactory.create()
        wish.command_results = []  # Clear any existing command results
        return wish

    @pytest.fixture
    def tracker(self, executor, wish_saver):
        """Create a CommandStatusTracker instance."""
        return CommandStatusTracker(executor, wish_saver)

    def test_check_status(self, tracker, executor, wish):
        """Test check_status method.

        This test verifies that the check_status method correctly delegates
        to the CommandExecutor's check_running_commands method.
        """
        # Check status
        tracker.check_status(wish)

        # Verify that CommandExecutor.check_running_commands was called
        executor.check_running_commands.assert_called_once()

    def test_is_all_completed_not_all_done(self, tracker, wish):
        """Test is_all_completed method when not all commands are done.

        This test verifies that the is_all_completed method correctly returns
        (False, False) when some commands are still running.
        """
        # Add a command result that is still DOING
        result = MagicMock()
        result.state = CommandState.DOING
        result.num = 1
        wish.command_results.append(result)

        # Check if all commands are completed
        all_completed, any_failed = tracker.is_all_completed(wish)

        # Verify that all_completed is False and any_failed is False
        assert not all_completed
        assert not any_failed

    def test_is_all_completed_all_success(self, tracker, wish):
        """Test is_all_completed method when all commands succeed.

        This test verifies that the is_all_completed method correctly returns
        (True, False) when all commands have completed successfully.
        """
        # Add command results that are all SUCCESS
        for i in range(3):
            result = MagicMock()
            result.state = CommandState.SUCCESS
            result.num = i + 1
            wish.command_results.append(result)

        # Check if all commands are completed
        all_completed, any_failed = tracker.is_all_completed(wish)

        # Verify that all_completed is True and any_failed is False
        assert all_completed
        assert not any_failed

    def test_is_all_completed_some_failed(self, tracker, wish):
        """Test is_all_completed method when some commands fail.

        This test verifies that the is_all_completed method correctly returns
        (True, True) when all commands have completed but some have failed.
        """
        # Add command results with one FAILED
        result1 = MagicMock()
        result1.state = CommandState.SUCCESS
        result1.num = 1
        wish.command_results.append(result1)

        result2 = MagicMock()
        result2.state = CommandState.OTHERS
        result2.num = 2
        wish.command_results.append(result2)

        # Check if all commands are completed
        all_completed, any_failed = tracker.is_all_completed(wish)

        # Verify that all_completed is True and any_failed is True
        assert all_completed
        assert any_failed

    def test_update_wish_state_not_all_done(self, tracker, wish, wish_saver):
        """Test update_wish_state method when not all commands are done.

        This test verifies that the update_wish_state method does not update
        the wish state when some commands are still running.
        """
        # Add a command result that is still DOING
        result = MagicMock()
        result.state = CommandState.DOING
        result.num = 1
        wish.command_results.append(result)

        # Update wish state
        updated = tracker.update_wish_state(wish)

        # Verify that the wish state was not updated
        assert not updated
        assert not tracker.all_completed
        assert wish.state == WishState.DOING
        assert wish.finished_at is None

        # Verify that save_wish was not called
        wish_saver.assert_not_called()

    def test_update_wish_state_all_success(self, tracker, wish, wish_saver):
        """Test update_wish_state method when all commands succeed.

        This test verifies that the update_wish_state method correctly updates
        the wish state to DONE when all commands have completed successfully.
        """
        # Add command results that are all SUCCESS
        for i in range(3):
            result = MagicMock()
            result.state = CommandState.SUCCESS
            result.num = i + 1
            wish.command_results.append(result)

        # Mock UtcDatetime.now to return a fixed timestamp
        with patch.object(UtcDatetime, 'now', return_value='2023-01-01T12:00:00Z'):
            # Update wish state
            updated = tracker.update_wish_state(wish)

        # Verify that the wish state was updated
        assert updated
        assert tracker.all_completed
        assert wish.state == WishState.DONE
        assert wish.finished_at == '2023-01-01T12:00:00Z'

        # Verify that save_wish was called
        wish_saver.assert_called_once_with(wish)

    def test_update_wish_state_some_failed(self, tracker, wish, wish_saver):
        """Test update_wish_state method when some commands fail.

        This test verifies that the update_wish_state method correctly updates
        the wish state to FAILED when some commands have failed.
        """
        # Add command results with one FAILED
        result1 = MagicMock()
        result1.state = CommandState.SUCCESS
        result1.num = 1
        wish.command_results.append(result1)

        result2 = MagicMock()
        result2.state = CommandState.OTHERS
        result2.num = 2
        wish.command_results.append(result2)

        # Mock UtcDatetime.now to return a fixed timestamp
        with patch.object(UtcDatetime, 'now', return_value='2023-01-01T12:00:00Z'):
            # Update wish state
            updated = tracker.update_wish_state(wish)

        # Verify that the wish state was updated
        assert updated
        assert tracker.all_completed
        assert wish.state == WishState.FAILED
        assert wish.finished_at == '2023-01-01T12:00:00Z'

        # Verify that save_wish was called
        wish_saver.assert_called_once_with(wish)

    def test_get_completion_message_all_success(self, tracker, wish):
        """Test get_completion_message method when all commands succeed.

        This test verifies that the get_completion_message method returns the
        correct message when all commands have completed successfully.
        """
        # Add command results that are all SUCCESS
        for i in range(3):
            result = MagicMock()
            result.state = CommandState.SUCCESS
            result.num = i + 1
            wish.command_results.append(result)

        # Get completion message
        message = tracker.get_completion_message(wish)

        # Verify the message
        assert message == "All commands completed."

    def test_get_completion_message_some_failed(self, tracker, wish):
        """Test get_completion_message method when some commands fail.

        This test verifies that the get_completion_message method returns the
        correct message when some commands have failed.
        """
        # Add command results with one FAILED
        result1 = MagicMock()
        result1.state = CommandState.SUCCESS
        result1.num = 1
        wish.command_results.append(result1)

        result2 = MagicMock()
        result2.state = CommandState.OTHERS
        result2.num = 2
        wish.command_results.append(result2)

        # Get completion message
        message = tracker.get_completion_message(wish)

        # Verify the message
        assert message == "All commands completed. Some commands failed."
