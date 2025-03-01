"""Base Pane widget for wish-sh TUI."""

from textual.containers import Container
from textual.widgets import Static


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
    
    def update_title_and_content(self, title_id: str, content_id: str, title: str, content: str) -> None:
        """Update the title and content of the pane.
        
        Args:
            title_id: The ID of the title widget.
            content_id: The ID of the content widget.
            title: The new title text.
            content: The new content text.
        """
        try:
            # Update title
            title_widget = self.query_one(f"#{title_id}")
            if isinstance(title_widget, Static):
                title_widget.update(title)
            
            # Update content
            content_widget = self.query_one(f"#{content_id}")
            if isinstance(content_widget, Static):
                content_widget.update(content)
        except Exception as e:
            self.log(f"Error updating title and content: {e}")
