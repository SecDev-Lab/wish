import pytest
from unittest.mock import MagicMock, patch

from textual.app import App

from wish_models import Wish, WishState
from wish_sh.wish_manager import WishManager
from wish_sh.wish_tui import CommandSuggestion, CommandExecutionScreen


class TestCommandSuggestion:
    """Test for CommandSuggestion."""

    @pytest.fixture
    def wish(self):
        """Create a test wish."""
        wish = Wish.create("Test wish")
        wish.state = WishState.DOING
        return wish

    @pytest.fixture
    def commands(self):
        """Create test commands."""
        return ["echo 'Test command 1'", "echo 'Test command 2'"]

    @pytest.fixture
    def screen(self, wish, commands):
        """Create a CommandSuggestion instance."""
        return CommandSuggestion(wish, commands)

    def test_on_yes_button_pressed_passes_wish_manager(self, screen, wish, commands):
        """Test that on_yes_button_pressed passes the wish_manager to CommandExecutionScreen."""
        # TODO Remove this test (for debugging)
        # Mock the app property
        with patch.object(CommandSuggestion, 'app', new_callable=MagicMock) as mock_app:
            # Create a wish_manager
            wish_manager = MagicMock(spec=WishManager)
            mock_app.wish_manager = wish_manager
            
            # Mock the push_screen method
            mock_app.push_screen = MagicMock()
            
            # Call on_yes_button_pressed
            screen.on_yes_button_pressed()
            
            # Check that push_screen was called with CommandExecutionScreen
            # and the correct arguments
            mock_app.push_screen.assert_called_once()
            args, kwargs = mock_app.push_screen.call_args
            assert len(args) == 1
            assert isinstance(args[0], CommandExecutionScreen)
            assert args[0].wish == wish
            assert args[0].commands == commands
            assert args[0].wish_manager == wish_manager
