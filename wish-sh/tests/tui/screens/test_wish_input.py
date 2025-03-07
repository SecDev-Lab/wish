from unittest.mock import MagicMock, patch

from wish_models import WishState

from wish_sh.test_factories import WishInputFactory
from wish_sh.wish_tui import CommandSuggestion


class TestWishInput:
    """Test for WishInput."""

    def test_on_input_submitted_uses_wish_manager(self):
        """Test that on_input_submitted uses WishManager.generate_commands.

        This test verifies:
        1. The on_input_submitted method calls WishManager.generate_commands with the wish text
        2. A new Wish object is created with the correct text and state
        3. A CommandSuggestion screen is created with the wish and generated commands
        4. The app.push_screen method is called with the created screen
        """
        # Create a screen with mocked app and event
        wish_text = "Test wish"
        screen, app_mock, mock_event = WishInputFactory.create_with_mock_event(wish_text=wish_text)
        wish_manager = app_mock.wish_manager

        # Set up the mock commands
        mock_commands = ["echo 'Test command 1'", "echo 'Test command 2'"]
        wish_manager.generate_commands.return_value = (mock_commands, None)

        # Create a property mock
        app_property_mock = MagicMock()
        app_property_mock.__get__ = MagicMock(return_value=app_mock)

        # Patch the WishInput.app property
        with patch('wish_sh.wish_tui.WishInput.app', app_property_mock):
            # Call on_input_submitted
            screen.on_input_submitted(mock_event)

            # Check that generate_commands was called with the correct wish text
            wish_manager.generate_commands.assert_called_once_with(wish_text)

            # Check that push_screen was called with CommandSuggestion
            # and the correct arguments
            app_mock.push_screen.assert_called_once()
            args, kwargs = app_mock.push_screen.call_args
            assert len(args) == 1
            assert isinstance(args[0], CommandSuggestion)
            assert args[0].wish.wish == wish_text
            assert args[0].wish.state == WishState.DOING
            assert args[0].commands == mock_commands
