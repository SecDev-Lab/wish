"""Wish Select Pane widget for wish-sh TUI."""

from textual.app import ComposeResult
from textual.widgets import Static

from wish_sh.tui.widgets.base_pane import BasePane


class WishSelectPane(BasePane):
    """A pane for selecting wishes."""

    DEFAULT_CSS = """
    WishSelectPane {
        width: 30;
        height: 100%;
    }
    """

    def __init__(self, wishes=None, *args, **kwargs):
        """Initialize the WishSelectPane.
        
        Args:
            wishes: List of wishes to display.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(*args, **kwargs)
        self.wishes = wishes or []

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        yield Static("Wish Select", id="wish-select-title")
        
        if not self.wishes:
            yield Static("(No wishes available)", id="wish-select-content")
        else:
            for wish in self.wishes:
                yield Static(str(wish), id=f"wish-{id(wish)}")
