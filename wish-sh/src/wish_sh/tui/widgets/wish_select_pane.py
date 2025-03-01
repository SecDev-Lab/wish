"""Wish Select Pane widget for wish-sh TUI."""

from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Static


class WishSelectPane(Container):
    """A pane for selecting wishes."""

    DEFAULT_CSS = """
    WishSelectPane {
        width: 30;
        height: 100%;
        border: solid $primary;
        background: $surface;
        padding: 1;
    }
    
    WishSelectPane.active-pane {
        border: heavy $accent;
        background: $surface-lighten-1;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        yield Static("Wish Select", id="wish-select-title")
        yield Static("(Wishes will be listed here)", id="wish-select-content")
    
    def set_active(self, active: bool) -> None:
        """Set the active state of the pane."""
        if active:
            # ペーン自体のスタイル変更
            self.add_class("active-pane")
        else:
            # ペーン自体のスタイルを元に戻す
            self.remove_class("active-pane")
