"""Base Pane widget for wish-sh TUI."""

from textual.containers import Container


class BasePane(Container):
    """Base class for all panes in the application."""

    DEFAULT_CSS = """
    BasePane {
        width: 100%;
        height: 100%;
        border: solid $primary;
        background: $surface;
        padding: 1;
    }
    
    BasePane.active-pane {
        border: heavy $accent;
        background: $surface-lighten-1;
    }
    """

    def set_active(self, active: bool) -> None:
        """Set the active state of the pane.
        
        Args:
            active: Whether the pane should be active or not.
        """
        if active:
            self.add_class("active-pane")
        else:
            self.remove_class("active-pane")
