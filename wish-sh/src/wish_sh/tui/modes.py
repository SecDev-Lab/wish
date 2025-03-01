"""Mode definitions for wish-sh TUI."""

from enum import Enum, auto


class WishMode(Enum):
    """Enum representing the different modes of the wish-sh TUI."""
    NEW_WISH = auto()
    WISH_HISTORY = auto()
