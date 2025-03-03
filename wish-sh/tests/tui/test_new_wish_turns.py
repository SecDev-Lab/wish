"""Tests for NewWishTurns class."""

import pytest
from wish_models import Wish

from wish_sh.tui.new_wish_turns import NewWishState, NewWishEvent, NewWishTurns


class TestNewWishTurns:
    """Tests for NewWishTurns class."""

    def test_init(self):
        """Test initialization."""
        turns = NewWishTurns()
        assert turns.current_state == NewWishState.INPUT_WISH
        assert turns.current_wish is None
        assert turns.current_commands == []
        assert turns.selected_commands == []
        assert turns.wish_detail is None

    def test_transition(self):
        """Test state transitions."""
        turns = NewWishTurns()
        
        # INPUT_WISH -> SUGGEST_COMMANDS
        assert turns.transition(NewWishEvent.SUFFICIENT_WISH)
        assert turns.current_state == NewWishState.SUGGEST_COMMANDS
        
        # SUGGEST_COMMANDS -> CONFIRM_COMMANDS
        assert turns.transition(NewWishEvent.COMMANDS_ACCEPTED)
        assert turns.current_state == NewWishState.CONFIRM_COMMANDS
        
        # CONFIRM_COMMANDS -> EXECUTE_COMMANDS
        assert turns.transition(NewWishEvent.EXECUTION_CONFIRMED)
        assert turns.current_state == NewWishState.EXECUTE_COMMANDS
        
        # EXECUTE_COMMANDS -> INPUT_WISH
        assert turns.transition(NewWishEvent.BACK_TO_INPUT)
        assert turns.current_state == NewWishState.INPUT_WISH
        
        # INPUT_WISH -> ASK_WISH_DETAIL
        assert turns.transition(NewWishEvent.INSUFFICIENT_WISH)
        assert turns.current_state == NewWishState.ASK_WISH_DETAIL
        
        # ASK_WISH_DETAIL -> SUGGEST_COMMANDS
        assert turns.transition(NewWishEvent.DETAIL_PROVIDED)
        assert turns.current_state == NewWishState.SUGGEST_COMMANDS
        
        # SUGGEST_COMMANDS -> ADJUST_COMMANDS
        assert turns.transition(NewWishEvent.ADJUSTMENT_REQUESTED)
        assert turns.current_state == NewWishState.ADJUST_COMMANDS
        
        # ADJUST_COMMANDS -> SUGGEST_COMMANDS
        assert turns.transition(NewWishEvent.COMMANDS_ADJUSTED)
        assert turns.current_state == NewWishState.SUGGEST_COMMANDS

    def test_invalid_transition(self):
        """Test invalid state transitions."""
        turns = NewWishTurns()
        
        # INPUT_WISH -> EXECUTE_COMMANDS (invalid)
        assert not turns.transition(NewWishEvent.EXECUTION_CONFIRMED)
        assert turns.current_state == NewWishState.INPUT_WISH

    def test_set_get_current_wish(self):
        """Test setting and getting current wish."""
        turns = NewWishTurns()
        wish = Wish.create("scan all ports")
        
        turns.set_current_wish(wish)
        assert turns.get_current_wish() == wish

    def test_set_get_current_commands(self):
        """Test setting and getting current commands."""
        turns = NewWishTurns()
        commands = ["nmap -p- 10.10.10.40", "nmap -sU 10.10.10.40"]
        
        turns.set_current_commands(commands)
        assert turns.get_current_commands() == commands

    def test_set_get_selected_commands(self):
        """Test setting and getting selected commands."""
        turns = NewWishTurns()
        commands = ["nmap -p- 10.10.10.40"]
        
        turns.set_selected_commands(commands)
        assert turns.get_selected_commands() == commands

    def test_set_get_wish_detail(self):
        """Test setting and getting wish detail."""
        turns = NewWishTurns()
        detail = "10.10.10.40"
        
        turns.set_wish_detail(detail)
        assert turns.get_wish_detail() == detail

    def test_handler(self):
        """Test registering and calling handlers."""
        turns = NewWishTurns()
        
        # Define a handler that returns an event
        def handler():
            return NewWishEvent.SUFFICIENT_WISH
        
        # Register the handler
        turns.register_handler(NewWishState.INPUT_WISH, handler)
        
        # Call the handler
        event = turns.handle_current_state()
        assert event == NewWishEvent.SUFFICIENT_WISH
