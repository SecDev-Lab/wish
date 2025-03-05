"""Factory for CommandExecutionScreen."""

import factory
from unittest.mock import MagicMock

from textual.widgets import Static

from wish_models import Wish, WishState
from wish_models.test_factories import WishDoingFactory
from wish_sh.wish_tui import CommandExecutionScreen
from wish_sh.test_factories.wish_manager_factory import WishManagerFactory


class CommandExecutionScreenFactory(factory.Factory):
    """Factory for CommandExecutionScreen."""

    class Meta:
        model = CommandExecutionScreen

    wish = factory.SubFactory(WishDoingFactory)
    commands = factory.List([
        "echo 'Test command 1'",
        "echo 'Test command 2'"
    ])
    wish_manager = factory.SubFactory(WishManagerFactory, create_strategy=factory.CREATE_STRATEGY_BUILD)

    @classmethod
    def create(cls, **kwargs):
        """Create a CommandExecutionScreen instance."""
        screen = super().create(**kwargs)
        return screen

    @classmethod
    def create_with_mocked_ui(cls, **kwargs):
        """Create a CommandExecutionScreen with mocked UI methods."""
        screen = cls.create(**kwargs)
        
        # Mock the set_interval method to avoid timer issues in tests
        screen.set_interval = MagicMock()
        
        # Mock the query_one method to return a mock Static widget
        status_widget = MagicMock(spec=Static)
        execution_text = MagicMock(spec=Static)
        
        def query_one_side_effect(selector):
            if selector == "#execution-text":
                return execution_text
            else:
                return status_widget
                
        screen.query_one = MagicMock(side_effect=query_one_side_effect)
        
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
