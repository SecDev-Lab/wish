"""Main Pane widget for wish-sh TUI."""

from textual.app import ComposeResult
from textual.widgets import Static

from wish_models import CommandState
from wish_sh.tui.widgets.base_pane import BasePane


class MainPane(BasePane):
    """Main content pane."""

    DEFAULT_CSS = """
    MainPane {
        width: 100%;
        height: 100%;
    }
    
    MainPane #command-status-done {
        color: $success;
    }
    
    MainPane #command-status-doing {
        color: $warning;
    }
    
    MainPane #command-status-failed, MainPane #command-status-cancelled {
        color: $error;
    }
    """

    def __init__(self, *args, **kwargs):
        """Initialize the MainPane.
        
        Args:
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(*args, **kwargs)
        self.current_wish = None

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        yield Static("Main Pane", id="main-pane-title")
        yield Static("(Main content will be displayed here)", id="main-pane-content")
    
    def update_wish(self, wish):
        """Update the pane with the selected wish details.
        
        Args:
            wish: The wish to display.
        """
        self.current_wish = wish
        
        # Get existing content widget
        content_widget = self.query_one("#main-pane-content")
        
        # Create content text
        if wish:
            # Format wish details
            content_lines = [
                f"wish: {wish.wish}",
                "",
                "Commands:"
            ]
            
            # Add command results
            for i, cmd in enumerate(wish.command_results, 1):
                status_id = ""
                if cmd.state == CommandState.SUCCESS:
                    status = "(DONE)"
                    status_id = "command-status-done"
                elif cmd.state == CommandState.OTHERS:
                    status = "(FAILED)"
                    status_id = "command-status-failed"
                elif cmd.state == CommandState.USER_CANCELLED:
                    status = "(CANCELLED)"
                    status_id = "command-status-cancelled"
                else:
                    status = "(DOING)"
                    status_id = "command-status-doing"
                
                command_line = f"({i}) {cmd.command}  {status}"
                content_lines.append(command_line)
            
            content_text = "\n".join(content_lines)
        else:
            content_text = "(No wish selected)"
        
        # Update the existing content widget
        content_widget.update(content_text)
