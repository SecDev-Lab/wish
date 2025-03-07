from enum import Enum


class CommandState(str, Enum):
    """Enumeration of ExitClass."""

    DOING = "DOING"
    """The command is being executed."""

    SUCCESS = "SUCCESS"
    """The command succeeded, with meaningful insights."""

    USER_CANCELLED = "USER_CANCELLED"
    """The user cancelled the command.

    Wish uses this state (wish assists human operators)"""

    COMMAND_NOT_FOUND = "COMMAND_NOT_FOUND"
    """The command was not found on the local machine."""

    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    """A file was not found on the local machine."""

    REMOTE_OPERATION_FAILED = "REMOTE_OPERATION_FAILED"
    """An operation on a remote machine failed."""

    TIMEOUT = "TIMEOUT"
    """The command timed out."""

    NETWORK_ERROR = "NETWORK_ERROR"
    """A network error occurred."""

    API_ERROR = "API_ERROR"
    """An error occurred when calling an external API."""

    OTHERS = "OTHERS"
    """Other errors."""
