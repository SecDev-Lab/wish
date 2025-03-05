"""Factory for CommandExecutionScreen."""

import asyncio
from unittest.mock import MagicMock

import factory
from textual.widgets import Static
from wish_models.test_factories import WishDoingFactory

from wish_sh.test_factories.wish_manager_factory import WishManagerFactory
from wish_sh.wish_tui import CommandExecutionScreen


class CommandExecutionScreenFactory(factory.Factory):
    """Factory for CommandExecutionScreen."""

    class Meta:
        model = CommandExecutionScreen

    wish = factory.SubFactory(WishDoingFactory)
    commands = factory.List([
        "echo 'Test command 1'",
        "echo 'Test command 2'"
    ])
    wish_manager = factory.SubFactory(WishManagerFactory, create_strategy=factory.CREATE_STRATEGY)

    @classmethod
    def create(cls, **kwargs):
        """Create a CommandExecutionScreen instance."""
        screen = super().create(**kwargs)
        return screen

    @classmethod
    def create_with_mocked_ui(cls, **kwargs):
        """Create a CommandExecutionScreen with mocked UI methods."""
        from wish_models import WishState

        screen = cls.create(**kwargs)

        # Mock asyncio.create_task to avoid async issues in tests
        screen._original_create_task = asyncio.create_task
        asyncio.create_task = MagicMock()

        # Mock the set_interval method for backward compatibility
        screen.set_interval = MagicMock()

        # Mock the monitor_commands method to avoid async issues
        screen.monitor_commands = MagicMock()

        # Mock the query_one method to return a mock Static widget
        status_widget = MagicMock(spec=Static)
        execution_text = MagicMock(spec=Static)

        def query_one_side_effect(selector):
            if selector == "#execution-text":
                return execution_text
            elif selector.startswith("#command-status-"):
                return status_widget
            else:
                return MagicMock()

        screen.query_one = MagicMock(side_effect=query_one_side_effect)

        # Ensure that ui_updater.show_completion_message calls execution_text.update
        original_show_completion_message = screen.ui_updater.show_completion_message

        def show_completion_message_side_effect(message):
            original_show_completion_message(message)
            execution_text.update(message)

        screen.ui_updater.show_completion_message = MagicMock(side_effect=show_completion_message_side_effect)

        # Mock the check_all_commands_completed method to properly update the wish state
        original_check_all_commands_completed = screen.check_all_commands_completed

        def check_all_commands_completed_side_effect():
            # Call the original method
            result = original_check_all_commands_completed()

            # If the tracker.is_all_completed method is mocked, use its return value
            if hasattr(screen.tracker.is_all_completed, 'return_value'):
                all_completed, any_failed = screen.tracker.is_all_completed.return_value

                if all_completed:
                    screen.all_completed = True

                    # Update wish state
                    if any_failed:
                        screen.wish.state = WishState.FAILED
                    else:
                        screen.wish.state = WishState.DONE

                    # Set finished_at
                    from wish_models import UtcDatetime
                    screen.wish.finished_at = UtcDatetime.now()

                    # Save wish to history
                    if hasattr(screen.wish_manager, 'save_wish'):
                        screen.wish_manager.save_wish(screen.wish)

                    # Show completion message
                    if hasattr(screen.tracker, 'get_completion_message'):
                        message = screen.tracker.get_completion_message(screen.wish)
                        screen.ui_updater.show_completion_message(message)

            return result

        screen.check_all_commands_completed = MagicMock(side_effect=check_all_commands_completed_side_effect)

        return screen, status_widget, execution_text

    @classmethod
    def create_with_sleep_commands(cls, durations=None, **kwargs):
        """Create a CommandExecutionScreen with sleep commands."""
        if durations is None:
            durations = [1, 2]

        commands = [f"sleep {duration}" for duration in durations]

        # Use WishManagerFactory with mock execute
        wish_manager = WishManagerFactory.create_with_mock_execute()

        return cls.create(
            commands=commands,
            wish_manager=wish_manager,
            **kwargs
        )
