"""Base Pane widget for wish-sh TUI."""

from textual.containers import Container


class BasePane(Container):
    """Base class for all panes in the application."""

    # CSS moved to external file: wish_tui.css

    def set_active(self, active: bool) -> None:
        """Set the active state of the pane.
        
        Args:
            active: Whether the pane should be active or not.
        """
        if active:
            self.add_class("active-pane")
        else:
            self.remove_class("active-pane")
