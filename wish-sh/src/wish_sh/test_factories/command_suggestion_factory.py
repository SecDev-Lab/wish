"""Factory for CommandSuggestion."""

from unittest.mock import MagicMock, patch

import factory
from wish_models.test_factories import WishDoingFactory

from wish_sh.test_factories.wish_manager_factory import WishManagerFactory
from wish_sh.wish_tui import CommandSuggestion


class CommandSuggestionFactory(factory.Factory):
    """Factory for CommandSuggestion."""

    class Meta:
        model = CommandSuggestion

    wish = factory.SubFactory(WishDoingFactory)
    commands = factory.List([
        "echo 'Test command 1'",
        "echo 'Test command 2'"
    ])

    @classmethod
    def create(cls, **kwargs):
        """Create a CommandSuggestion instance."""
        screen = super().create(**kwargs)
        return screen

    @classmethod
    def create_with_mocked_app(cls, **kwargs):
        """Create a CommandSuggestion with mocked app."""
        screen = cls.create(**kwargs)

        # Mock the app property
        app_mock = MagicMock()

        # Add wish_manager to the app
        app_mock.wish_manager = WishManagerFactory.create_with_simple_mocks()

        # Mock the push_screen method
        app_mock.push_screen = MagicMock()

        # Patch the app property
        with patch.object(CommandSuggestion, 'app', new_callable=MagicMock) as mock_app:
            mock_app.return_value = app_mock
            screen.app = app_mock

        return screen, app_mock
