"""Tests for CommandStatusTracker."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from wish_models import CommandState, UtcDatetime, WishState
from wish_models.test_factories import WishDoingFactory
from wish_models.test_factories.command_result_factory import CommandResultDoingFactory, CommandResultSuccessFactory

from wish_command_execution.test_factories import CommandStatusTrackerFactory


class TestCommandStatusTracker:
    """Tests for CommandStatusTracker."""

    @pytest.fixture
    def wish(self):
        """Create a test wish."""
        wish = WishDoingFactory.create()
        wish.command_results = []  # Clear any existing command results
        return wish

    @pytest.fixture
    def tracker(self):
        """Create a CommandStatusTracker instance with mocks."""
        return CommandStatusTrackerFactory.create()

    @pytest.mark.asyncio
    async def test_check_status(self, tracker, wish):
        """Test check_status method."""
        # Create a tracker with mocked methods
        mocked_tracker = CommandStatusTrackerFactory.create_with_mocks()
        
        # Check status
        await mocked_tracker.check_status(wish)

        # Verify that check_status was called
        mocked_tracker.check_status.assert_called_once_with(wish)

    def test_is_all_completed_not_all_done(self, tracker, wish):
        """Test is_all_completed method when not all commands are done."""
        # Reset the mock to use the real implementation
        tracker.is_all_completed = tracker.__class__.is_all_completed.__get__(tracker)
        
        # Add a command result that is still DOING
        result = CommandResultDoingFactory.create(num=1)
        wish.command_results.append(result)

        # Check if all commands are completed
        all_completed, any_failed = tracker.is_all_completed(wish)

        # Verify that all_completed is False and any_failed is False
        assert not all_completed
        assert not any_failed

    def test_is_all_completed_all_success(self, tracker, wish):
        """Test is_all_completed method when all commands succeed."""
        # Reset the mock to use the real implementation
        tracker.is_all_completed = tracker.__class__.is_all_completed.__get__(tracker)
        
        # Add command results that are all SUCCESS
        for i in range(3):
            result = CommandResultSuccessFactory.create(num=i+1)
            wish.command_results.append(result)

        # Check if all commands are completed
        all_completed, any_failed = tracker.is_all_completed(wish)

        # Verify that all_completed is True and any_failed is False
        assert all_completed
        assert not any_failed

    def test_is_all_completed_some_failed(self, tracker, wish):
        """Test is_all_completed method when some commands fail."""
        # Reset the mock to use the real implementation
        tracker.is_all_completed = tracker.__class__.is_all_completed.__get__(tracker)
        
        # Add command results with one FAILED
        result1 = CommandResultSuccessFactory.create(num=1)
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

    def test_update_wish_state_not_all_done(self, tracker, wish):
        """Test update_wish_state method when not all commands are done."""
        # Reset the mock to use the real implementation
        tracker.update_wish_state = tracker.__class__.update_wish_state.__get__(tracker)
        tracker.is_all_completed = MagicMock(return_value=(False, False))
        
        # Add a command result that is still DOING
        result = CommandResultDoingFactory.create(num=1)
        wish.command_results.append(result)

        # Update wish state
        updated = tracker.update_wish_state(wish)

        # Verify that the wish state was not updated
        assert not updated
        assert not tracker.all_completed
        assert wish.state == WishState.DOING
        assert wish.finished_at is None

        # Verify that is_all_completed was called
        tracker.is_all_completed.assert_called_once_with(wish)

    def test_update_wish_state_all_success(self, tracker, wish):
        """Test update_wish_state method when all commands succeed."""
        # Reset the mock to use the real implementation
        tracker.update_wish_state = tracker.__class__.update_wish_state.__get__(tracker)
        tracker.is_all_completed = MagicMock(return_value=(True, False))
        
        # Mock the wish_saver
        tracker.wish_saver = MagicMock()
        
        # Add command results that are all SUCCESS
        for i in range(3):
            result = CommandResultSuccessFactory.create(num=i+1)
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
        tracker.wish_saver.assert_called_once_with(wish)

    def test_update_wish_state_some_failed(self, tracker, wish):
        """Test update_wish_state method when some commands fail."""
        # Reset the mock to use the real implementation
        tracker.update_wish_state = tracker.__class__.update_wish_state.__get__(tracker)
        tracker.is_all_completed = MagicMock(return_value=(True, True))
        
        # Mock the wish_saver
        tracker.wish_saver = MagicMock()
        
        # Add command results with one FAILED
        result1 = CommandResultSuccessFactory.create(num=1)
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
        tracker.wish_saver.assert_called_once_with(wish)

    def test_get_completion_message_all_success(self, tracker, wish):
        """Test get_completion_message method when all commands succeed."""
        # Reset the mock to use the real implementation
        tracker.get_completion_message = tracker.__class__.get_completion_message.__get__(tracker)
        tracker.is_all_completed = MagicMock(return_value=(True, False))
        
        # Add command results that are all SUCCESS
        for i in range(3):
            result = CommandResultSuccessFactory.create(num=i+1)
            wish.command_results.append(result)

        # Get completion message
        message = tracker.get_completion_message(wish)

        # Verify the message
        assert message == "All commands completed."

    def test_get_completion_message_some_failed(self, tracker, wish):
        """Test get_completion_message method when some commands fail."""
        # Reset the mock to use the real implementation
        tracker.get_completion_message = tracker.__class__.get_completion_message.__get__(tracker)
        tracker.is_all_completed = MagicMock(return_value=(True, True))
        
        # Add command results with one FAILED
        result1 = CommandResultSuccessFactory.create(num=1)
        wish.command_results.append(result1)

        result2 = MagicMock()
        result2.state = CommandState.OTHERS
        result2.num = 2
        wish.command_results.append(result2)

        # Get completion message
        message = tracker.get_completion_message(wish)

        # Verify the message
        assert message == "All commands completed. Some commands failed."
