"""Message classes for New Wish mode in TUI."""

from typing import List

from textual.message import Message


class WishInputSubmitted(Message):
    """Message sent when a wish is submitted."""

    def __init__(self, wish_text: str):
        """Initialize the message.
        
        Args:
            wish_text: The submitted wish text.
        """
        self.wish_text = wish_text
        super().__init__()


class WishDetailSubmitted(Message):
    """Message sent when wish detail is submitted."""

    def __init__(self, detail: str):
        """Initialize the message.
        
        Args:
            detail: The submitted detail text.
        """
        self.detail = detail
        super().__init__()


class CommandsAccepted(Message):
    """Message sent when commands are accepted."""
    pass


class CommandsRejected(Message):
    """Message sent when commands are rejected."""
    pass


class CommandAdjustRequested(Message):
    """Message sent when command adjustment is requested."""
    pass


class CommandsAdjusted(Message):
    """Message sent when commands are adjusted."""

    def __init__(self, commands: List[str]):
        """Initialize the message.
        
        Args:
            commands: The adjusted commands.
        """
        self.commands = commands
        super().__init__()


class CommandAdjustCancelled(Message):
    """Message sent when command adjustment is cancelled."""
    pass


class ExecutionConfirmed(Message):
    """Message sent when command execution is confirmed."""
    pass


class ExecutionCancelled(Message):
    """Message sent when command execution is cancelled."""
    pass
