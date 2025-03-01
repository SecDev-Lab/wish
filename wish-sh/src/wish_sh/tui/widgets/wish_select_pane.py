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
    
    WishSelectPane:focus-within {
        border: heavy $accent;
        background: $accent-lighten-2;
    }
    
    #wish-select-active-title {
        color: $success;
        text-style: bold;
    }
    
    #wish-select-inactive-title {
        color: $text;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        self.active_title = Static("[Active] Wish Select", id="wish-select-active-title")
        self.inactive_title = Static("Wish Select", id="wish-select-inactive-title")
        
        # Initially, Wish Select pane is inactive
        self.active_title.styles.display = "none"
        self.inactive_title.styles.display = "block"
        
        yield self.active_title
        yield self.inactive_title
        yield Static("(Wishes will be listed here)", id="wish-select-content")
    
    def set_active(self, active: bool) -> None:
        """Set the active state of the pane."""
        if active:
            self.active_title.styles.display = "block"
            self.inactive_title.styles.display = "none"
        else:
            self.active_title.styles.display = "none"
            self.inactive_title.styles.display = "block"
