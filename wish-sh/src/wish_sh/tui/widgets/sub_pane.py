"""Sub Pane widget for wish-sh TUI."""

from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Static


class SubPane(Container):
    """Sub content pane."""

    DEFAULT_CSS = """
    SubPane {
        width: 100%;
        height: 100%;
        border: solid $primary;
        background: $surface;
        padding: 1;
    }
    
    SubPane.active-pane {
        border: heavy $accent;
        background: $surface-lighten-1;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        yield Static("Sub Pane", id="sub-pane-title")
        yield Static("(Sub content will be displayed here)", id="sub-pane-content")
    
    def set_active(self, active: bool) -> None:
        """Set the active state of the pane."""
        if active:
            # ペーン自体のスタイル変更
            self.add_class("active-pane")
        else:
            # ペーン自体のスタイルを元に戻す
            self.remove_class("active-pane")
