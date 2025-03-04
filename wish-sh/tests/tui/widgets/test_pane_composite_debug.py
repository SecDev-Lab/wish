"""Debug tests for PaneComposite."""

import pytest
from unittest.mock import MagicMock, patch

from wish_sh.tui.new_wish_turns import NewWishTurns, NewWishState, NewWishEvent
from wish_sh.tui.widgets.pane_composite import NewWishPaneComposite


class TestNewWishPaneCompositeDebug:
    """Debug tests for NewWishPaneComposite."""

    def test_update_for_suggest_commands_state(self):
        """
        TODO Remove this test (for debugging)
        
        Test that update_for_state correctly updates sub_pane for SUGGEST_COMMANDS state.
        """
        # Arrange
        main_pane = MagicMock()
        sub_pane = MagicMock()
        composite = NewWishPaneComposite(main_pane, sub_pane)
        
        # Mock the app property
        main_pane.app = MagicMock()
        
        # Set up the state
        composite.new_wish_turns.current_state = NewWishState.SUGGEST_COMMANDS
        
        # Set up test commands
        test_commands = ["command1", "command2"]
        composite.new_wish_turns.set_current_commands(test_commands)
        
        # Act
        composite.update_for_state()
        
        # Assert
        main_pane.update_for_suggest_commands.assert_called_once_with(test_commands)
        sub_pane.update_for_suggest_commands.assert_called_once_with(test_commands)
    
    def test_handle_wish_input_sufficient(self):
        """
        TODO Remove this test (for debugging)
        
        Test that handle_wish_input correctly transitions to SUGGEST_COMMANDS for sufficient wish.
        """
        # Arrange
        main_pane = MagicMock()
        sub_pane = MagicMock()
        composite = NewWishPaneComposite(main_pane, sub_pane)
        
        # Mock the app property
        main_pane.app = MagicMock()
        
        # Mock is_wish_sufficient to return True
        composite.is_wish_sufficient = MagicMock(return_value=True)
        
        # Mock the necessary methods and objects
        with patch('wish_sh.wish_manager.WishManager') as mock_manager_class:
            mock_manager = mock_manager_class.return_value
            mock_manager.generate_commands.return_value = ["command1", "command2"]
            
            # Mock Wish
            with patch('wish_models.Wish') as mock_wish_class:
                mock_wish = mock_wish_class.create.return_value
                
                # Act
                composite.handle_wish_input("test wish")
                
                # Assert
                assert composite.new_wish_turns.current_state == NewWishState.SUGGEST_COMMANDS
                mock_manager.generate_commands.assert_called_once_with("test wish")
                main_pane.update_for_suggest_commands.assert_called_once()
                sub_pane.update_for_suggest_commands.assert_called_once()
