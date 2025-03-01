"""Main Pane widget for wish-sh TUI."""

from datetime import datetime
from textual.app import ComposeResult
from textual.message import Message
from textual.widgets import Static

from wish_models import CommandState, CommandResult, WishState, UtcDatetime
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
        yield Static("(Main content will be displayed here)", id="main-pane-content", markup=True)
    
    def update_for_new_wish_mode(self):
        """Update the pane for New Wish mode."""
        content_widget = self.query_one("#main-pane-content")
        content_widget.update("[b]新しいWishを作成するモードです。[/b]")
    
    def _get_wish_state_emoji(self, state):
        """Get emoji for wish state."""
        if state == WishState.DOING:
            return "🔄"
        elif state == WishState.DONE:
            return "✅"
        elif state == WishState.FAILED:
            return "❌"
        elif state == WishState.CANCELLED:
            return "🚫"
        else:
            return "❓"

    def _get_command_state_emoji(self, state):
        """Get emoji for command state."""
        if state == CommandState.DOING:
            return "🔄"
        elif state == CommandState.SUCCESS:
            return "✅"
        elif state == CommandState.USER_CANCELLED:
            return "🚫"
        elif state == CommandState.COMMAND_NOT_FOUND:
            return "🔍❌"
        elif state == CommandState.FILE_NOT_FOUND:
            return "📄❌"
        elif state == CommandState.REMOTE_OPERATION_FAILED:
            return "🌐❌"
        elif state == CommandState.TIMEOUT:
            return "⏱️"
        elif state == CommandState.NETWORK_ERROR:
            return "📡❌"
        elif state == CommandState.OTHERS:
            return "❌"
        else:
            return "❓"
    
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
                # Get emoji for wish state
                state_emoji = self._get_wish_state_emoji(wish.state)
                
                # Convert UTC times to local time
                if isinstance(wish.created_at, str):
                    # Convert string to UtcDatetime
                    created_at_dt = UtcDatetime.model_validate(wish.created_at)
                    created_at_local = created_at_dt.to_local_str()
                else:
                    created_at_local = wish.created_at.to_local_str()
                
                finished_at_text = "(Not finished yet)"
                if wish.finished_at:
                    if isinstance(wish.finished_at, str):
                        # Convert string to UtcDatetime
                        finished_at_dt = UtcDatetime.model_validate(wish.finished_at)
                        finished_at_text = finished_at_dt.to_local_str()
                    else:
                        finished_at_text = wish.finished_at.to_local_str()
                
                # Format wish details with aligned labels
                content_lines = [
                    f"[b]Wish:[/b]     {wish.wish}",
                    f"[b]Status:[/b]   {state_emoji} {wish.state}",
                    f"[b]Created:[/b]  {created_at_local}",
                    f"[b]Finished:[/b] {finished_at_text}",
                    "",
                    "[b]Commands:[/b]"
                ]
                
                # Add command results as single lines
                for i, cmd in enumerate(wish.command_results, 1):
                    cmd_emoji = self._get_command_state_emoji(cmd.state)
                    content_lines.append(f"{cmd_emoji} ({i}) {cmd.command}")
                
                content_text = "\n".join(content_lines)
            else:
                content_text = "(No wish selected)"
            
            # Update the existing content widget
            content_widget.update(content_text)
        except Exception as e:
            error_message = f"Error updating wish: {e}"
            self.log(error_message)
            try:
                content_widget = self.query_one("#main-pane-content")
                content_widget.update(f"(Error displaying wish details: {e})")
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
            # First 6 lines are header (Wish, Status, Created, Finished, empty line, "Commands:")
            header_lines = 6
            if clicked_line >= header_lines and clicked_line < header_lines + len(self.current_wish.command_results):
                command_index = clicked_line - header_lines
                if 0 <= command_index < len(self.current_wish.command_results):
                    selected_command = self.current_wish.command_results[command_index]
                    # Post a message that a command was selected
                    self.post_message(CommandSelected(selected_command))
        except Exception as e:
            self.log(f"Error handling click: {e}")
