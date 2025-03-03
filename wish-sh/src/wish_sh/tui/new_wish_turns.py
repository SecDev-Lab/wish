"""State machine for New Wish mode in TUI."""

from enum import Enum, auto
from typing import Callable, Dict, List, Optional

from wish_models import Wish


class NewWishState(Enum):
    """Enumeration of states in the New Wish state machine"""
    INPUT_WISH = auto()
    ASK_WISH_DETAIL = auto()
    SUGGEST_COMMANDS = auto()
    SELECT_COMMANDS = auto()
    ADJUST_COMMANDS = auto()
    CONFIRM_COMMANDS = auto()
    EXECUTE_COMMANDS = auto()


class NewWishEvent(Enum):
    """Enumeration of events in the New Wish state machine"""
    SUFFICIENT_WISH = auto()
    INSUFFICIENT_WISH = auto()
    DETAIL_PROVIDED = auto()
    COMMANDS_ACCEPTED = auto()
    COMMANDS_REJECTED = auto()
    COMMANDS_ADJUSTED = auto()
    ADJUSTMENT_REQUESTED = auto()
    EXECUTION_CONFIRMED = auto()
    EXECUTION_CANCELLED = auto()
    BACK_TO_INPUT = auto()


class NewWishTurns:
    """Implementation of the New Wish state machine for TUI"""

    def __init__(self):
        self.current_state = NewWishState.INPUT_WISH
        self.current_wish: Optional[Wish] = None
        self.current_commands: List[str] = []
        self.selected_commands: List[str] = []
        self.wish_detail: Optional[str] = None

        # Initialize the state transition table
        self.transitions: Dict[NewWishState, Dict[NewWishEvent, NewWishState]] = {
            NewWishState.INPUT_WISH: {
                NewWishEvent.SUFFICIENT_WISH: NewWishState.SUGGEST_COMMANDS,
                NewWishEvent.INSUFFICIENT_WISH: NewWishState.ASK_WISH_DETAIL,
            },
            NewWishState.ASK_WISH_DETAIL: {
                NewWishEvent.DETAIL_PROVIDED: NewWishState.SUGGEST_COMMANDS,
                NewWishEvent.BACK_TO_INPUT: NewWishState.INPUT_WISH,
            },
            NewWishState.SUGGEST_COMMANDS: {
                NewWishEvent.COMMANDS_ACCEPTED: NewWishState.CONFIRM_COMMANDS,
                NewWishEvent.COMMANDS_REJECTED: NewWishState.INPUT_WISH,
                NewWishEvent.ADJUSTMENT_REQUESTED: NewWishState.ADJUST_COMMANDS,
            },
            NewWishState.ADJUST_COMMANDS: {
                NewWishEvent.COMMANDS_ADJUSTED: NewWishState.SUGGEST_COMMANDS,
                NewWishEvent.BACK_TO_INPUT: NewWishState.INPUT_WISH,
            },
            NewWishState.CONFIRM_COMMANDS: {
                NewWishEvent.EXECUTION_CONFIRMED: NewWishState.EXECUTE_COMMANDS,
                NewWishEvent.EXECUTION_CANCELLED: NewWishState.INPUT_WISH,
            },
            NewWishState.EXECUTE_COMMANDS: {
                NewWishEvent.BACK_TO_INPUT: NewWishState.INPUT_WISH,
            },
        }

        # Handler functions for each state
        self.state_handlers: Dict[NewWishState, Callable] = {}

    def register_handler(self, state: NewWishState, handler: Callable):
        """Register a handler function for a state"""
        self.state_handlers[state] = handler

    def transition(self, event: NewWishEvent) -> bool:
        """Transition to a new state based on the event

        Returns:
            bool: Whether the transition was successful
        """
        if event in self.transitions.get(self.current_state, {}):
            self.current_state = self.transitions[self.current_state][event]
            return True
        return False

    def handle_current_state(self) -> Optional[NewWishEvent]:
        """Execute the handler function for the current state

        Returns:
            Optional[NewWishEvent]: The event returned by the handler (if any)
        """
        if self.current_state in self.state_handlers:
            return self.state_handlers[self.current_state]()
        return None

    def set_current_wish(self, wish: Wish):
        """Set the current wish"""
        self.current_wish = wish

    def set_current_commands(self, commands: List[str]):
        """Set the current command list"""
        self.current_commands = commands

    def set_selected_commands(self, commands: List[str]):
        """Set the selected command list"""
        self.selected_commands = commands

    def set_wish_detail(self, detail: str):
        """Set the wish detail"""
        self.wish_detail = detail

    def get_current_wish(self) -> Optional[Wish]:
        """Get the current wish"""
        return self.current_wish

    def get_current_commands(self) -> List[str]:
        """Get the current command list"""
        return self.current_commands

    def get_selected_commands(self) -> List[str]:
        """Get the selected command list"""
        return self.selected_commands

    def get_wish_detail(self) -> Optional[str]:
        """Get the wish detail"""
        return self.wish_detail
