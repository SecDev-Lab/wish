from unittest.mock import MagicMock, patch

from wish_sh.test_factories import CommandSuggestionFactory
from wish_sh.wish_tui import CommandExecutionScreen


class TestCommandSuggestion:
    """Test for CommandSuggestion."""

    def test_on_yes_button_pressed_passes_wish_manager(self):
        """Test that on_yes_button_pressed passes the wish_manager to CommandExecutionScreen.

        This test verifies:
        1. The on_yes_button_pressed method creates a CommandExecutionScreen
        2. The wish, commands, and wish_manager are correctly passed to the screen
        3. The app.push_screen method is called with the created screen
        """
        # Create a screen with mocked app
        screen, app_mock = CommandSuggestionFactory.create_with_mocked_app()
        wish_manager = app_mock.wish_manager

        # Create a property mock
        app_property_mock = MagicMock()
        app_property_mock.__get__ = MagicMock(return_value=app_mock)

        # Patch the CommandSuggestion.app property
        with patch('wish_sh.wish_tui.CommandSuggestion.app', app_property_mock):
            # Call on_yes_button_pressed
            screen.on_yes_button_pressed()

            # Check that push_screen was called with CommandExecutionScreen
            # and the correct arguments
            app_mock.push_screen.assert_called_once()
            args, kwargs = app_mock.push_screen.call_args
            assert len(args) == 1
            assert isinstance(args[0], CommandExecutionScreen)
            assert args[0].wish == screen.wish
            assert args[0].commands == screen.commands
            assert args[0].wish_manager == wish_manager
