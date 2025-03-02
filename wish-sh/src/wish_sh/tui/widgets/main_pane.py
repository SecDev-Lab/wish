"""Main Pane widget for wish-sh TUI."""

from datetime import datetime
from textual.app import ComposeResult
from textual.message import Message
from textual.widgets import Static
from textual.containers import Horizontal, Vertical

from wish_models import CommandState, CommandResult, WishState, UtcDatetime
from wish_sh.tui.utils import make_markup_safe, sanitize_command_text
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
        self.selected_command_index = -1  # -1 means no command selected
        self.command_indices = []  # Store command indices for click handling

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        yield Static("(Main content will be displayed here)", id="main-pane-content", markup=True)
    
    def update_for_new_wish_mode(self):
        """Update the pane for New Wish mode."""
        # Remove old grid if exists
        try:
            old_grid = self.query_one("#wish-details-grid")
            self.remove(old_grid)
        except Exception as e:
            self.logger.debug(f"No wish-details-grid to remove: {e}")
            
        self.update_content("main-pane-content", "[b]新しいWishを作成するモードです。[/b]")
    
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
    
    def _format_datetime(self, dt):
        """Format a datetime for display.
        
        Args:
            dt: The datetime to format, can be string or UtcDatetime.
            
        Returns:
            str: The formatted datetime string.
        """
        if isinstance(dt, str):
            # Convert string to UtcDatetime
            dt_obj = UtcDatetime.model_validate(dt)
            return dt_obj.to_local_str()
        else:
            return dt.to_local_str()
    
    def _create_content_lines(self, wish, state_emoji, created_at_local, finished_at_text):
        """Create content lines for display.
        
        Args:
            wish: The wish to display.
            state_emoji: The emoji for the wish state.
            created_at_local: The local created time.
            finished_at_text: The finished time text.
            
        Returns:
            list: The content lines.
            list: The command indices.
        """
        content_lines = []
        
        # Add wish details with label and value on the same line
        content_lines.append(f"Wish:     {wish.wish}")
        content_lines.append(f"Status:   {state_emoji} {wish.state}")
        content_lines.append(f"Created:  {created_at_local}")
        content_lines.append(f"Finished: {finished_at_text}")
        content_lines.append("")
        content_lines.append("Commands:")
        
        # Add command results
        command_indices = []  # Store command indices for click handling
        for i, cmd in enumerate(wish.command_results, 1):
            cmd_emoji = self._get_command_state_emoji(cmd.state)
            safe_command = sanitize_command_text(cmd.command)
            
            # Add command with CSS class for selection instead of '>' character
            cmd_index = i - 1
            cmd_text = f"{cmd_emoji} ({i}) {safe_command}"
            
            # Store line indices for commands
            cmd_line_index = len(content_lines)  # Index of the command line
            command_indices.append((i-1, cmd_line_index))
            
            # Add the command line with visual indicator for selection
            if cmd_index == self.selected_command_index:
                # Use standard Rich markup for selected command
                content_lines.append(f"[reverse]{cmd_text}[/reverse]")
            else:
                content_lines.append(cmd_text)
        
        return content_lines, command_indices
    
    def update_wish(self, wish, preserve_selection=False):
        """Update the pane with the selected wish details.
        
        Args:
            wish: The wish to display.
            preserve_selection: Whether to preserve the current selection.
        """
        try:
            # Check if the wish has changed
            wish_changed = self.current_wish != wish
            self.current_wish = wish
            
            # Reset selection conditions:
            # 1. If the wish has changed and preserve_selection is False
            # 2. If preserve_selection is False (force reset even for the same wish)
            if not preserve_selection:
                self.logger.debug(f"Resetting selection because preserve_selection={preserve_selection}")
                self.selected_command_index = -1  # Default to no selection
                
                # If wish has commands, select the first one (index 0)
                if wish and wish.command_results and len(wish.command_results) > 0:
                    self.selected_command_index = 0
            
            self.logger.debug(f"update_wish: selected_command_index={self.selected_command_index}, preserve_selection={preserve_selection}")
            
            # Get existing content widget
            content_widget = self.get_content_widget("main-pane-content")
            
            if wish:
                # Get emoji for wish state
                state_emoji = self._get_wish_state_emoji(wish.state)
                
                # Convert UTC times to local time
                created_at_local = self._format_datetime(wish.created_at)
                
                finished_at_text = "(Not finished yet)"
                if wish.finished_at:
                    finished_at_text = self._format_datetime(wish.finished_at)
                
                # Remove old grid if exists (but keep the content widget)
                try:
                    old_grid = self.query_one("#wish-details-grid")
                    self.remove(old_grid)
                except Exception as e:
                    self.logger.debug(f"No wish-details-grid to remove: {e}")
                
                # Create content lines and command indices
                content_lines, self.command_indices = self._create_content_lines(
                    wish, state_emoji, created_at_local, finished_at_text
                )
                
                # Update the existing content widget with markup enabled for CSS classes
                content_widget.markup = True
                content_widget.update("\n".join(content_lines))
                
                # Force a refresh to ensure the UI updates
                self.refresh()
            else:
                # If no wish selected, show simple message
                self.update_content("main-pane-content", "(No wish selected)")
        except Exception as e:
            error_message = f"Error updating wish: {e}"
            self.logger.error(error_message)
            try:
                self.update_content("main-pane-content", f"(Error displaying wish details: {e})")
            except Exception as inner_e:
                # Minimal error handling if we can't even get the content widget
                self.logger.error(f"Failed to display error message: {inner_e}")
    
    def on_key(self, event) -> None:
        """Handle key events for command selection."""
        # Check conditions and log
        if not self.current_wish:
            self.logger.debug("on_key: No current wish")
            return False
        if not self.current_wish.command_results:
            self.logger.debug("on_key: No command results")
            return False

        if event.key in ("up", "arrow_up"):
            self.logger.debug(f"on_key: Up key pressed, current index: {self.selected_command_index}")
            self.select_previous_command()
            return True
        elif event.key in ("down", "arrow_down"):
            self.logger.debug(f"on_key: Down key pressed, current index: {self.selected_command_index}")
            self.select_next_command()
            return True
        
        return False
    
    def select_previous_command(self) -> None:
        """Select the previous command."""
        if self.selected_command_index > 0:
            self.selected_command_index -= 1
            self.update_command_selection()
    
    def select_next_command(self) -> None:
        """Select the next command."""
        if self.selected_command_index < len(self.current_wish.command_results) - 1:
            self.selected_command_index += 1
            self.update_command_selection()
        elif self.selected_command_index == -1 and len(self.current_wish.command_results) > 0:
            # If no command is selected yet, select the first one
            self.selected_command_index = 0
            self.update_command_selection()
    
    def update_command_selection(self) -> None:
        """Update the command selection and post a message."""
        if 0 <= self.selected_command_index < len(self.current_wish.command_results):
            selected_command = self.current_wish.command_results[self.selected_command_index]
            # Post a message that a command was selected
            self.post_message(CommandSelected(selected_command))
            
            # Update display with preserved selection
            self.logger.debug(f"update_command_selection: selected_command_index={self.selected_command_index}")
            self.update_wish(self.current_wish, preserve_selection=True)
    
    def on_click(self, event) -> None:
        """Handle click events to select commands."""
        # Check conditions and log
        if not self.current_wish:
            self.logger.debug("on_click: No current wish")
            return
        if not self.current_wish.command_results:
            self.logger.debug("on_click: No command results")
            return
        
        try:
            # Get the clicked line
            content_widget = self.query_one("#main-pane-content")
            clicked_line = event.y - content_widget.region.y
            self.logger.debug(f"on_click: Clicked line: {clicked_line}")
            
            # Check if we clicked on a command line
            for cmd_index, line_index in self.command_indices:
                if clicked_line == line_index or clicked_line == line_index + 1:  # Command line or command text line
                    if 0 <= cmd_index < len(self.current_wish.command_results):
                        self.logger.debug(f"on_click: Selected command index: {cmd_index}")
                        self.selected_command_index = cmd_index
                        selected_command = self.current_wish.command_results[cmd_index]
                        # Post a message that a command was selected
                        self.post_message(CommandSelected(selected_command))
                        # Update display with preserved selection
                        self.update_wish(self.current_wish, preserve_selection=True)
                        break
        except Exception as e:
            self.logger.error(f"Error handling click: {e}")
