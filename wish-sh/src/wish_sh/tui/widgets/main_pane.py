"""Main Pane widget for wish-sh TUI."""

from textual.app import ComposeResult
from textual.widgets import Static

from wish_sh.tui.widgets.base_pane import BasePane


class MainPane(BasePane):
    """Main content pane."""

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        yield Static("Main Pane", id="main-pane-title")
        yield Static("(Main content will be displayed here)", id="main-pane-content")
