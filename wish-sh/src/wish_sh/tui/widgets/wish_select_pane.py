"""Wish Select Pane widget for wish-sh TUI."""

from textual.app import ComposeResult
from textual.widgets import Static

from wish_sh.tui.widgets.base_pane import BasePane
from wish_sh.wish_manager import WishManager


class WishSelectPane(BasePane):
    """A pane for selecting wishes."""

    DEFAULT_CSS = """
    WishSelectPane {
        width: 30;
        height: 100%;
    }
    """

    def __init__(self, wishes=None, manager=None, *args, **kwargs):
        """Initialize the WishSelectPane.
        
        Args:
            wishes: List of wishes to display.
            manager: WishManager instance for formatting wishes.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(*args, **kwargs)
        self.wishes = wishes or []
        self.manager = manager

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        yield Static("Wish Select", id="wish-select-title", markup=False)
        
        if not self.wishes:
            yield Static("(No wishes available)", id="wish-select-content", markup=False)
        else:
            for i, wish in enumerate(self.wishes, 1):
                # Use a simple representation to avoid markup issues
                yield Static(f"[{i}] {wish.wish}", id=f"wish-{id(wish)}", markup=False)
