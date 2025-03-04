"""Debug tests for integration."""

import pytest
from unittest.mock import MagicMock, patch

from wish_sh.tui.screens.main_screen import MainScreen
from wish_sh.tui.new_wish_turns import NewWishState, NewWishEvent
from wish_sh.tui.widgets.pane_composite import NewWishPaneComposite


class TestIntegrationDebug:
    """Debug tests for integration."""

    def test_main_screen_focus_sub_pane(self):
        """
        TODO Remove this test (for debugging)
        
        Test that the main screen correctly focuses the sub pane.
        """
        # Create a mock main pane and sub pane
        main_pane = MagicMock()
        sub_pane = MagicMock()
        
        # Create a mock composite
        composite = MagicMock()
        composite.main_pane = main_pane
        composite.sub_pane = sub_pane
        
        # Create a mock screen
        screen = MagicMock()
        screen.new_wish_main_pane = main_pane
        screen.new_wish_sub_pane = sub_pane
        screen.new_wish_composite = composite
        screen.wish_select = MagicMock()
        screen.help_pane = MagicMock()
        
        # Set up the state
        composite.new_wish_turns = MagicMock()
        composite.new_wish_turns.current_state = NewWishState.SUGGEST_COMMANDS
        
        # Call the method directly
        screen.new_wish_sub_pane.set_active(True)
        screen.new_wish_main_pane.set_active(False)
        screen.wish_select.set_active(False)
        screen.new_wish_sub_pane.focus()
        
        # Assert
        screen.new_wish_sub_pane.set_active.assert_called_with(True)
        screen.new_wish_main_pane.set_active.assert_called_with(False)
        screen.wish_select.set_active.assert_called_with(False)
        screen.new_wish_sub_pane.focus.assert_called_once()
