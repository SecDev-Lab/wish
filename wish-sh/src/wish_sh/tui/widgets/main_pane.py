"""Main Pane widget for wish-sh TUI."""

from textual.app import ComposeResult
from textual.message import Message
from textual.widgets import Static

from wish_models import CommandState, CommandResult
from wish_sh.tui.widgets.base_pane import BasePane


class CommandSelected(Message):
    """Message sent when a command is selected."""

    def __init__(self, command_result: CommandResult):
        """Initialize the message.
        
        Args:
            command_result: The selected command result.
        """
        self.command_result = command_result
        super().__init__()


class MainPane(BasePane):
    """Main content pane."""

    # CSS moved to external file: wish_tui.css

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
        yield Static("(Main content will be displayed here)", id="main-pane-content")
    
    def update_for_new_wish_mode(self):
        """Update the pane for New Wish mode."""
        content_widget = self.query_one("#main-pane-content")
        content_widget.update("新しいWishを作成するモードです。")
    
    def update_wish(self, wish):
        """Update the pane with the selected wish details.
        
        Args:
            wish: The wish to display.
        """
        try:
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
        except Exception as e:
            self.log(f"Error updating wish: {e}")
            try:
                content_widget = self.query_one("#main-pane-content")
                content_widget.update("(Error displaying wish details)")
            except:
                # Minimal error handling if we can't even get the content widget
                pass
    
    def on_click(self, event) -> None:
        """Handle click events to select commands."""
        if not self.current_wish or not self.current_wish.command_results:
            return
        
        try:
            # Get the clicked line
            content_widget = self.query_one("#main-pane-content")
            clicked_line = event.y - content_widget.region.y
            
            # Calculate which command was clicked (if any)
            # First 3 lines are header (wish, empty line, "Commands:")
            if clicked_line >= 3 and clicked_line < 3 + len(self.current_wish.command_results):
                command_index = clicked_line - 3
                if 0 <= command_index < len(self.current_wish.command_results):
                    selected_command = self.current_wish.command_results[command_index]
                    # Post a message that a command was selected
                    self.post_message(CommandSelected(selected_command))
        except Exception as e:
            self.log(f"Error handling click: {e}")
