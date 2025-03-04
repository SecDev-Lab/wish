"""Debug tests for NewWishTurns."""

import pytest
from unittest.mock import MagicMock, patch

from wish_sh.tui.new_wish_turns import NewWishTurns, NewWishState, NewWishEvent


class TestNewWishTurnsDebug:
    """Debug tests for NewWishTurns."""

    def test_sufficient_wish_transition(self):
        """
        TODO Remove this test (for debugging)
        
        Test that the state transitions correctly for a sufficient wish.
        """
        # Arrange
        turns = NewWishTurns()
        
        # Act
        turns.transition(NewWishEvent.SUFFICIENT_WISH)
        
        # Assert
        assert turns.current_state == NewWishState.SUGGEST_COMMANDS
    
    def test_set_current_commands(self):
        """
        TODO Remove this test (for debugging)
        
        Test that set_current_commands correctly sets the commands.
        """
        # Arrange
        turns = NewWishTurns()
        commands = ["command1", "command2"]
        
        # Act
        turns.set_current_commands(commands)
        
        # Assert
        assert turns.get_current_commands() == commands
