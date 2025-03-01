"""Sub Pane widget for wish-sh TUI."""

from textual.app import ComposeResult
from textual.widgets import Static

from wish_sh.tui.widgets.base_pane import BasePane


class SubPane(BasePane):
    """Sub content pane."""

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        yield Static("Sub Pane", id="sub-pane-title")
        yield Static("(Sub content will be displayed here)", id="sub-pane-content")
