"""Help Pane widget for wish-sh TUI."""

from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Static


class HelpPane(Container):
    """Help information pane."""

    DEFAULT_CSS = """
    HelpPane {
        width: 100%;
        height: 3;
        dock: bottom;
        border: solid $primary;
        background: $surface-darken-1;
        padding: 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        yield Static(
            "Help: Ctrl+← Wish Select | Ctrl+↑ Main | Ctrl+↓ Sub | q 確認して終了 | Ctrl+Q 直接終了",
            id="help-content"
        )
