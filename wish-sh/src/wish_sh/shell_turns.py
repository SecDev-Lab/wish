from enum import Enum, auto
from typing import Callable, Dict, List, Optional

from wish_models import Wish


class ShellState(Enum):
    """Enumeration of states in the Shell Turns state machine"""

    INPUT_WISH = auto()
    ASK_WISH_DETAIL = auto()
    SUGGEST_COMMANDS = auto()
    CONFIRM_COMMANDS = auto()
    ADJUST_COMMANDS = auto()
    SHOW_WISHLIST = auto()
    SELECT_WISH = auto()
    SHOW_COMMANDS = auto()
    SELECT_COMMAND = auto()
    SELECT_COMMANDS = auto()
    SHOW_LOG_SUMMARY = auto()
    CANCEL_COMMANDS = auto()
    START_COMMANDS = auto()


class ShellEvent(Enum):
    """Enumeration of events in the Shell Turns state machine"""

    SUFFICIENT_WISH = auto()
    INSUFFICIENT_WISH = auto()
    OK = auto()
    NO = auto()
    CTRL_R = auto()  # wishlist
    CTRL_C = auto()  # cancel
    WISH_NUMBER = auto()
    SHOW_MORE = auto()
    MULTIPLE_COMMANDS = auto()
    SINGLE_COMMAND = auto()
    BACK_TO_INPUT = auto()


class ShellTurns:
    """Implementation of the Shell Turns state machine"""

    def __init__(self):
        self.current_state = ShellState.INPUT_WISH
        self.current_wish: Optional[Wish] = None
        self.current_commands: List[str] = []
        self.selected_commands: List[str] = []
        self.wishes: List[Wish] = []
        self.selected_wish_index: Optional[int] = None

        # Initialize the state transition table
        self.transitions: Dict[ShellState, Dict[ShellEvent, ShellState]] = {
            ShellState.INPUT_WISH: {
                ShellEvent.SUFFICIENT_WISH: ShellState.SUGGEST_COMMANDS,
                ShellEvent.INSUFFICIENT_WISH: ShellState.ASK_WISH_DETAIL,
                ShellEvent.CTRL_R: ShellState.SHOW_WISHLIST,
                ShellEvent.CTRL_C: ShellState.CANCEL_COMMANDS,
            },
            ShellState.ASK_WISH_DETAIL: {
                ShellEvent.OK: ShellState.SUGGEST_COMMANDS,
                ShellEvent.NO: ShellState.INPUT_WISH,
            },
            ShellState.SUGGEST_COMMANDS: {
                ShellEvent.OK: ShellState.CONFIRM_COMMANDS,
                ShellEvent.NO: ShellState.ADJUST_COMMANDS,
            },
            ShellState.CONFIRM_COMMANDS: {
                ShellEvent.OK: ShellState.START_COMMANDS,
                ShellEvent.NO: ShellState.INPUT_WISH,
            },
            ShellState.ADJUST_COMMANDS: {
                ShellEvent.OK: ShellState.SUGGEST_COMMANDS,
            },
            ShellState.SHOW_WISHLIST: {
                ShellEvent.WISH_NUMBER: ShellState.SELECT_WISH,
                ShellEvent.SHOW_MORE: ShellState.SHOW_WISHLIST,
                ShellEvent.BACK_TO_INPUT: ShellState.INPUT_WISH,
            },
            ShellState.SELECT_WISH: {
                ShellEvent.OK: ShellState.SHOW_COMMANDS,
            },
            ShellState.SHOW_COMMANDS: {
                ShellEvent.MULTIPLE_COMMANDS: ShellState.SELECT_COMMAND,
                ShellEvent.SINGLE_COMMAND: ShellState.SHOW_LOG_SUMMARY,
            },
            ShellState.SELECT_COMMAND: {
                ShellEvent.OK: ShellState.SHOW_LOG_SUMMARY,
            },
            ShellState.SELECT_COMMANDS: {
                ShellEvent.OK: ShellState.CANCEL_COMMANDS,
            },
            ShellState.SHOW_LOG_SUMMARY: {
                ShellEvent.BACK_TO_INPUT: ShellState.INPUT_WISH,
            },
            ShellState.CANCEL_COMMANDS: {
                ShellEvent.BACK_TO_INPUT: ShellState.INPUT_WISH,
            },
            ShellState.START_COMMANDS: {
                ShellEvent.BACK_TO_INPUT: ShellState.INPUT_WISH,
            },
        }

        # Handler functions for each state
        self.state_handlers: Dict[ShellState, Callable] = {}

    def register_handler(self, state: ShellState, handler: Callable):
        """Register a handler function for a state"""
        self.state_handlers[state] = handler

    def transition(self, event: ShellEvent) -> bool:
        """Transition to a new state based on the event

        Returns:
            bool: Whether the transition was successful
        """
        if event in self.transitions.get(self.current_state, {}):
            self.current_state = self.transitions[self.current_state][event]
            return True
        return False

    def handle_current_state(self) -> Optional[ShellEvent]:
        """Execute the handler function for the current state

        Returns:
            Optional[ShellEvent]: The event returned by the handler (if any)
        """
        if self.current_state in self.state_handlers:
            return self.state_handlers[self.current_state]()
        return None

    def run(self):
        """Run the state machine"""
        while True:
            event = self.handle_current_state()
            if event:
                self.transition(event)

    def set_current_wish(self, wish: Wish):
        """Set the current wish"""
        self.current_wish = wish

    def set_current_commands(self, commands: List[str]):
        """Set the current command list"""
        self.current_commands = commands

    def set_selected_commands(self, commands: List[str]):
        """Set the selected command list"""
        self.selected_commands = commands

    def set_wishes(self, wishes: List[Wish]):
        """Set the wish list"""
        self.wishes = wishes

    def set_selected_wish_index(self, index: int):
        """Set the index of the selected wish"""
        self.selected_wish_index = index

    def get_current_wish(self) -> Optional[Wish]:
        """Get the current wish"""
        return self.current_wish

    def get_current_commands(self) -> List[str]:
        """Get the current command list"""
        return self.current_commands

    def get_selected_commands(self) -> List[str]:
        """Get the selected command list"""
        return self.selected_commands

    def get_wishes(self) -> List[Wish]:
        """Get the wish list"""
        return self.wishes

    def get_selected_wish(self) -> Optional[Wish]:
        """Get the selected wish"""
        if self.selected_wish_index is not None and 0 <= self.selected_wish_index < len(self.wishes):
            return self.wishes[self.selected_wish_index]
        return None
