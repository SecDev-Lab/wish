from unittest.mock import MagicMock, call

import pytest
from wish_models import Wish

from wish_sh.shell_turns import ShellEvent, ShellState, ShellTurns


class TestShellTurns:
    def test_initialization(self):
        """Test that ShellTurns initializes with the correct attributes."""
        turns = ShellTurns()

        # Check initial state
        assert turns.current_state == ShellState.INPUT_WISH
        assert turns.current_wish is None
        assert turns.current_commands == []
        assert turns.selected_commands == []
        assert turns.wishes == []
        assert turns.selected_wish_index is None
        assert isinstance(turns.transitions, dict)
        assert isinstance(turns.state_handlers, dict)

        # Check that all states have transitions defined
        for state in ShellState:
            assert state in turns.transitions

    def test_transition_valid(self):
        """Test that transition works with valid events."""
        turns = ShellTurns()

        # Test transition from INPUT_WISH to SUGGEST_COMMANDS
        assert turns.current_state == ShellState.INPUT_WISH
        result = turns.transition(ShellEvent.SUFFICIENT_WISH)
        assert result is True
        assert turns.current_state == ShellState.SUGGEST_COMMANDS

        # Test transition from SUGGEST_COMMANDS to CONFIRM_COMMANDS
        result = turns.transition(ShellEvent.OK)
        assert result is True
        assert turns.current_state == ShellState.CONFIRM_COMMANDS

        # Test transition from CONFIRM_COMMANDS to START_COMMANDS
        result = turns.transition(ShellEvent.OK)
        assert result is True
        assert turns.current_state == ShellState.START_COMMANDS

    def test_transition_invalid(self):
        """Test that transition handles invalid events."""
        turns = ShellTurns()

        # Test invalid transition from INPUT_WISH
        assert turns.current_state == ShellState.INPUT_WISH
        result = turns.transition(ShellEvent.SINGLE_COMMAND)  # Not valid for INPUT_WISH
        assert result is False
        assert turns.current_state == ShellState.INPUT_WISH  # State should not change

    def test_register_and_handle_state(self):
        """Test registering and handling state handlers."""
        turns = ShellTurns()

        # Create mock handlers
        mock_input_handler = MagicMock(return_value=ShellEvent.SUFFICIENT_WISH)
        mock_suggest_handler = MagicMock(return_value=ShellEvent.OK)

        # Register handlers
        turns.register_handler(ShellState.INPUT_WISH, mock_input_handler)
        turns.register_handler(ShellState.SUGGEST_COMMANDS, mock_suggest_handler)

        # Test handling INPUT_WISH state
        event = turns.handle_current_state()
        assert event == ShellEvent.SUFFICIENT_WISH
        mock_input_handler.assert_called_once()

        # Transition to SUGGEST_COMMANDS
        turns.transition(event)
        assert turns.current_state == ShellState.SUGGEST_COMMANDS

        # Test handling SUGGEST_COMMANDS state
        event = turns.handle_current_state()
        assert event == ShellEvent.OK
        mock_suggest_handler.assert_called_once()

    def test_handle_unregistered_state(self):
        """Test handling a state with no registered handler."""
        turns = ShellTurns()

        # No handlers registered
        event = turns.handle_current_state()
        assert event is None

    def test_run(self, monkeypatch):
        """Test the run method."""
        turns = ShellTurns()

        # Mock handle_current_state to return events for first two calls, then raise exception to exit loop
        mock_events = [ShellEvent.SUFFICIENT_WISH, ShellEvent.OK]
        mock_handle = MagicMock(side_effect=mock_events + [Exception("Stop loop")])
        monkeypatch.setattr(turns, "handle_current_state", mock_handle)

        # Mock transition method
        mock_transition = MagicMock()
        monkeypatch.setattr(turns, "transition", mock_transition)

        # Run should call handle_current_state and transition for each event
        with pytest.raises(Exception, match="Stop loop"):
            turns.run()

        assert mock_handle.call_count == 3
        assert mock_transition.call_count == 2
        mock_transition.assert_has_calls([
            call(ShellEvent.SUFFICIENT_WISH),
            call(ShellEvent.OK)
        ])

    def test_set_get_current_wish(self):
        """Test setting and getting the current wish."""
        turns = ShellTurns()

        # Initially None
        assert turns.get_current_wish() is None

        # Set and get
        wish = MagicMock(spec=Wish)
        turns.set_current_wish(wish)
        assert turns.get_current_wish() is wish

    def test_set_get_current_commands(self):
        """Test setting and getting the current commands."""
        turns = ShellTurns()

        # Initially empty
        assert turns.get_current_commands() == []

        # Set and get
        commands = ["command1", "command2"]
        turns.set_current_commands(commands)
        assert turns.get_current_commands() == commands

    def test_set_get_selected_commands(self):
        """Test setting and getting the selected commands."""
        turns = ShellTurns()

        # Initially empty
        assert turns.get_selected_commands() == []

        # Set and get
        commands = ["command1", "command2"]
        turns.set_selected_commands(commands)
        assert turns.get_selected_commands() == commands

    def test_set_get_wishes(self):
        """Test setting and getting the wishes list."""
        turns = ShellTurns()

        # Initially empty
        assert turns.get_wishes() == []

        # Set and get
        wishes = [MagicMock(spec=Wish), MagicMock(spec=Wish)]
        turns.set_wishes(wishes)
        assert turns.get_wishes() == wishes

    def test_set_get_selected_wish(self):
        """Test setting the selected wish index and getting the selected wish."""
        turns = ShellTurns()

        # Initially None
        assert turns.get_selected_wish() is None

        # Set wishes and index
        wishes = [MagicMock(spec=Wish), MagicMock(spec=Wish)]
        turns.set_wishes(wishes)

        # Valid index
        turns.set_selected_wish_index(0)
        assert turns.get_selected_wish() is wishes[0]

        turns.set_selected_wish_index(1)
        assert turns.get_selected_wish() is wishes[1]

        # Invalid index (out of range)
        turns.set_selected_wish_index(2)
        assert turns.get_selected_wish() is None

        # Invalid index (negative)
        turns.set_selected_wish_index(-1)
        assert turns.get_selected_wish() is None
