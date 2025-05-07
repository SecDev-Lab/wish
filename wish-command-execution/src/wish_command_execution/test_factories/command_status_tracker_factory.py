"""Factory for creating CommandStatusTracker instances for testing."""

from unittest.mock import AsyncMock, MagicMock

import factory

from wish_command_execution.command_status_tracker import CommandStatusTracker
from wish_command_execution.test_factories.command_executor_factory import CommandExecutorFactory


class CommandStatusTrackerFactory(factory.Factory):
    """Factory for creating CommandStatusTracker instances."""

    class Meta:
        model = CommandStatusTracker

    executor = factory.SubFactory(CommandExecutorFactory)
    wish_saver = factory.LazyFunction(lambda: MagicMock())

    @classmethod
    def create_with_mocks(cls, all_completed=False, **kwargs):
        """Create a CommandStatusTracker with mocked methods.

        Args:
            all_completed: Whether all commands are completed.
            **kwargs: Additional attributes to set on the tracker.

        Returns:
            CommandStatusTracker: A configured CommandStatusTracker instance with mocks.
        """
        tracker = cls.create(**kwargs)
        tracker.all_completed = all_completed

        # Mock methods
        tracker.check_status = AsyncMock()
        tracker.is_all_completed = MagicMock(return_value=(all_completed, False))
        tracker.update_wish_state = MagicMock(return_value=all_completed)
        tracker.get_completion_message = MagicMock(return_value="All commands completed.")

        return tracker
