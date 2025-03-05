import pytest
from unittest.mock import MagicMock, patch

from textual.widgets import Input

from wish_models import Wish, WishState
from wish_sh.wish_manager import WishManager
from wish_sh.wish_tui import CommandSuggestion, WishInput


class TestWishInput:
    """Test for WishInput."""

    @pytest.fixture
    def screen(self):
        """Create a WishInput instance."""
        return WishInput()

    def test_on_input_submitted_uses_wish_manager(self, screen):
        """Test that on_input_submitted uses WishManager.generate_commands."""
        # TODO Remove this test (for debugging)
        # Mock the app property
        with patch.object(WishInput, 'app', new_callable=MagicMock) as mock_app:
            # Create a wish_manager with a mocked generate_commands method
            wish_manager = MagicMock(spec=WishManager)
            mock_commands = ["echo 'Test command 1'", "echo 'Test command 2'"]
            wish_manager.generate_commands.return_value = mock_commands
            mock_app.wish_manager = wish_manager
            
            # Mock the push_screen method
            mock_app.push_screen = MagicMock()
            
            # Create a mock Input.Submitted event
            wish_text = "Test wish"
            mock_event = MagicMock(spec=Input.Submitted)
            mock_event.value = wish_text
            
            # Call on_input_submitted
            screen.on_input_submitted(mock_event)
            
            # Check that generate_commands was called with the correct wish text
            wish_manager.generate_commands.assert_called_once_with(wish_text)
            
            # Check that push_screen was called with CommandSuggestion
            # and the correct arguments
            mock_app.push_screen.assert_called_once()
            args, kwargs = mock_app.push_screen.call_args
            assert len(args) == 1
            assert isinstance(args[0], CommandSuggestion)
            assert args[0].wish.wish == wish_text
            assert args[0].wish.state == WishState.DOING
            assert args[0].commands == mock_commands
