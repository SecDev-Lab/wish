"""Base Pane widget for wish-sh TUI."""

from textual.containers import Container
from textual.widgets import Static

from wish_sh.logging import setup_logger
from wish_sh.tui.utils import make_markup_safe, sanitize_command_text


class BasePane(Container):
    """Base class for all panes in the application."""

    # CSS moved to external file: wish_tui.css

    def __init__(self, *args, **kwargs):
        """Initialize the BasePane.
        
        Args:
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(*args, **kwargs)
        # Set up logger for this pane
        self.logger = setup_logger(f"wish_sh.tui.{self.__class__.__name__}")

    def set_active(self, active: bool) -> None:
        """Set the active state of the pane.
        
        Args:
            active: Whether the pane should be active or not.
        """
        if active:
            self.add_class("active-pane")
            # Set focus to this pane
            self.focus()
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
            self.logger.error(f"Error updating title and content: {e}")
    
    def update_content(self, content_id: str, content: str, markup: bool = True) -> None:
        """Update the content of a widget.
        
        Args:
            content_id: The ID of the content widget.
            content: The new content text.
            markup: Whether to enable markup in the content.
        """
        try:
            content_widget = self.query_one(f"#{content_id}")
            if isinstance(content_widget, Static):
                content_widget.markup = markup
                content_widget.update(content)
        except Exception as e:
            self.logger.error(f"Error updating content: {e}")
    
    def get_content_widget(self, content_id: str) -> Static:
        """Get the content widget with the specified ID.
        
        Args:
            content_id: The ID of the content widget.
            
        Returns:
            The content widget.
        """
        try:
            return self.query_one(f"#{content_id}")
        except Exception as e:
            self.logger.error(f"Error getting content widget: {e}")
            # Create a new content widget if it doesn't exist
            content = Static(id=content_id)
            self.mount(content)
            return content
