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
    
    SubPane:focus-within {
        border: heavy $accent;
        background: $accent-lighten-2;
    }
    
    #sub-pane-active-title {
        color: $success;
        text-style: bold;
    }
    
    #sub-pane-inactive-title {
        color: $text;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        self.active_title = Static("[Active] Sub Pane", id="sub-pane-active-title")
        self.inactive_title = Static("Sub Pane", id="sub-pane-inactive-title")
        
        # Initially, Sub pane is inactive
        self.active_title.styles.display = "none"
        self.inactive_title.styles.display = "block"
        
        yield self.active_title
        yield self.inactive_title
        yield Static("(Sub content will be displayed here)", id="sub-pane-content")
    
    def set_active(self, active: bool) -> None:
        """Set the active state of the pane."""
        if active:
            self.active_title.styles.display = "block"
            self.inactive_title.styles.display = "none"
        else:
            self.active_title.styles.display = "none"
            self.inactive_title.styles.display = "block"
