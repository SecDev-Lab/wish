"""Factory for WishInput."""

from unittest.mock import MagicMock, patch

import factory
from textual.widgets import Input

from wish_sh.test_factories.wish_manager_factory import WishManagerFactory
from wish_sh.wish_tui import WishInput


class WishInputFactory(factory.Factory):
    """Factory for WishInput."""

    class Meta:
        model = WishInput

    @classmethod
    def create(cls, **kwargs):
        """Create a WishInput instance."""
        screen = super().create(**kwargs)
        return screen

    @classmethod
    def create_with_mocked_app(cls, **kwargs):
        """Create a WishInput with mocked app."""
        screen = cls.create(**kwargs)

        # Mock the app property
        app_mock = MagicMock()

        # Add wish_manager to the app
        app_mock.wish_manager = WishManagerFactory.create_with_simple_mocks()

        # Mock the push_screen method
        app_mock.push_screen = MagicMock()

        # Patch the app property
        with patch.object(WishInput, 'app', new_callable=MagicMock) as mock_app:
            mock_app.return_value = app_mock
            screen.app = app_mock

        return screen, app_mock

    @classmethod
    def create_with_mock_event(cls, wish_text="Test wish", **kwargs):
        """Create a WishInput with a mock Input.Submitted event."""
        screen, app_mock = cls.create_with_mocked_app(**kwargs)

        # Create a mock Input.Submitted event
        mock_event = MagicMock(spec=Input.Submitted)
        mock_event.value = wish_text

        return screen, app_mock, mock_event
