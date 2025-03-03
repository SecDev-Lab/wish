"""Sub Pane widget for wish-sh TUI."""

import os
from datetime import datetime, timezone
from textual.app import ComposeResult
from textual.widgets import Static
from textual.containers import Horizontal

from wish_models.command_result.command_state import CommandState
from wish_sh.tui.utils import make_markup_safe, sanitize_command_text, get_command_state_emoji
from wish_sh.tui.widgets.base_pane import BasePane


class SubPane(BasePane):
    """Sub content pane for displaying command output details."""

    # Message constants
    MSG_NO_COMMAND_SELECTED = "(Select a command to view details)"
    MSG_NEW_WISH_MODE = "Command output for new Wish will be displayed here"
    MSG_NO_OUTPUT_FILE = "(No output file available)"
    MSG_NO_ERROR_FILE = "(No error output file available)"
    MSG_NO_OUTPUT = "(No output)"
    MSG_FILE_NOT_FOUND_PREFIX = "(File not found: "
    MSG_ERROR_READING_FILE_PREFIX = "(Error reading file: "
    MSG_VIEW_FULL_OUTPUT = "... (Press 'o' to view full output)"
    MSG_VIEW_FULL_ERROR = "... (Press 'e' to view full error output)"

    # CSS moved to external file: wish_tui.css

    def __init__(self, *args, **kwargs):
        """Initialize the SubPane.
        
        Args:
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(*args, **kwargs)
        self.current_command = None

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        yield Static(self.MSG_NO_COMMAND_SELECTED, id="sub-pane-content")
    
    def update_for_new_wish_mode(self):
        """Update the pane for New Wish mode."""
        # Remove old grid if exists
        try:
            old_grid = self.query_one("#command-details-grid")
            self.remove(old_grid)
        except Exception as e:
            self.logger.debug(f"No command-details-grid to remove: {e}")
            
        self.update_content("sub-pane-content", self.MSG_NEW_WISH_MODE)
    
    # New Wish mode state-specific update methods
    def update_for_input_wish(self):
        """Update for INPUT_WISH state."""
        self.update_content("sub-pane-content", "Please enter your Wish. Example: scan all ports")
    
    def update_for_ask_wish_detail(self):
        """Update for ASK_WISH_DETAIL state."""
        self.update_content("sub-pane-content", "Please enter the target IP address or hostname.")
    
    def update_for_suggest_commands(self):
        """Update for SUGGEST_COMMANDS state."""
        self.update_content("sub-pane-content", "Please check the commands and choose whether to execute them.")
    
    def update_for_adjust_commands(self):
        """Update for ADJUST_COMMANDS state."""
        self.update_content("sub-pane-content", "Please modify the commands.")
    
    def update_for_confirm_commands(self):
        """Update for CONFIRM_COMMANDS state."""
        self.update_content("sub-pane-content", "Please confirm the execution of commands.")
    
    def update_for_execute_commands(self):
        """Update for EXECUTE_COMMANDS state."""
        self.update_content("sub-pane-content", "Executing commands. Please wait a moment.")
    
    def set_active(self, active: bool) -> None:
        """Set the active state of the pane.
        
        Args:
            active: Whether the pane should be active or not.
        """
        super().set_active(active)
        
        if active:
            # Focus the content widget
            try:
                content = self.query_one("#sub-pane-content")
                content.focus()
                self.logger.debug("SubPane content focused")
            except Exception as e:
                self.logger.error(f"Error focusing content: {e}")
    
    def on_key(self, event) -> None:
        """Process key events.
        
        Args:
            event: The key event.
            
        Returns:
            bool: True if the event was handled, False otherwise.
        """
        self.logger.debug(f"Key event: {event.key}, focused: {self.has_focus}, "
                         f"active: {self.has_class('active-pane')}, "
                         f"current_command: {self.current_command is not None}")
        
        # Handle 'o' key to show stdout in log viewer
        if event.key == "o" and self.current_command:
            self.logger.debug(f"'o' key pressed with current_command")
            # Show stdout popup
            if self.current_command.log_files and self.current_command.log_files.stdout:
                try:
                    if os.path.exists(self.current_command.log_files.stdout):
                        with open(self.current_command.log_files.stdout, "r") as f:
                            stdout_content = f.read()
                        
                        # Show popup dialog
                        from wish_sh.tui.screens.log_viewer_screen import LogViewerScreen
                        self.app.push_screen(
                            LogViewerScreen(stdout_content, "Standard Output")
                        )
                        return True
                except Exception as e:
                    self.logger.error(f"Error reading stdout: {e}")
            return True
        
        # Handle 'e' key to show stderr in log viewer
        elif event.key == "e" and self.current_command:
            self.logger.debug(f"'e' key pressed with current_command")
            # Show stderr popup
            if self.current_command.log_files and self.current_command.log_files.stderr:
                try:
                    if os.path.exists(self.current_command.log_files.stderr):
                        with open(self.current_command.log_files.stderr, "r") as f:
                            stderr_content = f.read()
                        
                        # Show popup dialog
                        from wish_sh.tui.screens.log_viewer_screen import LogViewerScreen
                        self.app.push_screen(
                            LogViewerScreen(stderr_content, "Standard Error")
                        )
                        return True
                except Exception as e:
                    self.logger.error(f"Error reading stderr: {e}")
            return True
        
        # Handle scrolling keys
        elif event.key in ("j", "down"):
            content = self.query_one("#sub-pane-content")
            content.scroll_down()
            self.logger.debug("Scrolling down")
            return True
        elif event.key in ("k", "up"):
            content = self.query_one("#sub-pane-content")
            content.scroll_up()
            self.logger.debug("Scrolling up")
            return True
        elif event.key == "ctrl+f":
            content = self.query_one("#sub-pane-content")
            content.scroll_page_down()
            self.logger.debug("Page down")
            return True
        elif event.key == "ctrl+b":
            content = self.query_one("#sub-pane-content")
            content.scroll_page_up()
            self.logger.debug("Page up")
            return True
        elif event.key == "<":
            content = self.query_one("#sub-pane-content")
            content.scroll_home()
            self.logger.debug("Scroll to top")
            return True
        elif event.key == ">":
            content = self.query_one("#sub-pane-content")
            content.scroll_end()
            self.logger.debug("Scroll to bottom")
            return True
        
        return False
    
    def _read_log_file(self, file_path, max_preview_lines=3):
        """Read a log file and return its contents.
        
        Args:
            file_path: The path to the log file.
            max_preview_lines: Maximum number of lines to return for preview.
            
        Returns:
            tuple: (lines, line_count, preview_lines)
        """
        try:
            if not os.path.exists(file_path):
                return [], 0, [f"{self.MSG_FILE_NOT_FOUND_PREFIX}{file_path})"]
                
            with open(file_path, "r") as f:
                lines = f.readlines()
                
            if not lines:
                return [], 0, [self.MSG_NO_OUTPUT]
                
            # Get preview lines (first few lines)
            preview_lines = []
            for line in lines[:max_preview_lines]:
                safe_line = sanitize_command_text(line.rstrip())
                preview_lines.append(safe_line)
                
            return lines, len(lines), preview_lines
        except Exception as e:
            self.logger.error(f"Error reading log file: {e}")
            return [], 0, [f"{self.MSG_ERROR_READING_FILE_PREFIX}{e})"]
    
    def _get_state_display(self, state):
        """Get a human-readable display for command state.
        
        Args:
            state: The CommandState enum value.
            
        Returns:
            tuple: (display_text, style_class)
        """
        if state is None:
            return "Unknown", "state-unknown"
            
        state_map = {
            CommandState.DOING: ("Running", "state-doing"),
            CommandState.SUCCESS: ("Success", "state-success"),
            CommandState.USER_CANCELLED: ("User Cancelled", "state-cancelled"),
            CommandState.COMMAND_NOT_FOUND: ("Command Not Found", "state-error"),
            CommandState.FILE_NOT_FOUND: ("File Not Found", "state-error"),
            CommandState.REMOTE_OPERATION_FAILED: ("Remote Operation Failed", "state-error"),
            CommandState.TIMEOUT: ("Timeout", "state-error"),
            CommandState.NETWORK_ERROR: ("Network Error", "state-error"),
            CommandState.OTHERS: ("Other Error", "state-error"),
        }
        
        return state_map.get(state, ("Unknown", "state-unknown"))
    
    def _format_duration(self, start_time, end_time):
        """Format the duration between two UTC timestamps.
        
        Args:
            start_time: The start time (UtcDatetime).
            end_time: The end time (UtcDatetime).
            
        Returns:
            str: Formatted duration string.
        """
        if not start_time or not end_time:
            return "Unknown"
            
        # Convert to datetime objects
        start_dt = start_time.v
        end_dt = end_time.v
        
        # Calculate duration
        duration = end_dt - start_dt
        
        # Format duration
        total_seconds = duration.total_seconds()
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if hours > 0:
            return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
        elif minutes > 0:
            return f"{int(minutes)}m {int(seconds)}s"
        else:
            return f"{int(seconds)}s"
    
    def update_command_output(self, command_result):
        """Update the pane with command output details.
        
        Args:
            command_result: The command result to display.
        """
        try:
            self.logger.debug(f"Updating command output: {command_result is not None}")
            self.current_command = command_result
            
            # Get content widget
            content_widget = self.get_content_widget("sub-pane-content")
            
            if not command_result:
                content_widget.update(self.MSG_NO_COMMAND_SELECTED)
                return
            
            # Create content lines for the widget
            content_lines = []
            
            # Command information section
            safe_command = sanitize_command_text(command_result.command)
            content_lines.append(f"Command:    #{command_result.num} {safe_command}")
            
            # Status
            state_text, state_class = self._get_state_display(command_result.state)
            state_emoji = get_command_state_emoji(command_result.state)
            content_lines.append(f"Status:     {state_emoji} {state_text}")
            
            # Exit code (if command is finished)
            if command_result.exit_code is not None:
                content_lines.append(f"Exit Code:  {command_result.exit_code}")
            

            # Start time
            if command_result.created_at:
                try:
                    # If it's a UtcDatetime object
                    if hasattr(command_result.created_at, 'to_local_str'):
                        local_created_at = command_result.created_at.to_local_str("%Y-%m-%d %H:%M:%S")
                    # If it's a string
                    else:
                        local_created_at = str(command_result.created_at)
                    content_lines.append(f"Started:    {local_created_at}")
                except Exception as e:
                    self.logger.error(f"Error formatting created_at: {e}")
                    content_lines.append(f"Started:    {str(command_result.created_at)}")
            
            # End time (if command is finished)
            if command_result.finished_at:
                try:
                    # If it's a UtcDatetime object
                    if hasattr(command_result.finished_at, 'to_local_str'):
                        local_finished_at = command_result.finished_at.to_local_str("%Y-%m-%d %H:%M:%S")
                    # If it's a string
                    else:
                        local_finished_at = str(command_result.finished_at)
                    content_lines.append(f"Finished:   {local_finished_at}")
                    
                    # Duration
                    if hasattr(command_result.created_at, 'v') and hasattr(command_result.finished_at, 'v'):
                        duration = self._format_duration(command_result.created_at, command_result.finished_at)
                        content_lines.append(f"Duration:   {duration}")
                except Exception as e:
                    self.logger.error(f"Error formatting finished_at: {e}")
                    content_lines.append(f"Finished:   {str(command_result.finished_at)}")
            
            # Log summary section
            if command_result.log_summary:
                content_lines.append("")
                content_lines.append("=== Log Summary ===")
                content_lines.append(command_result.log_summary)
            
            # Output section
            content_lines.append("")
            content_lines.append("=== Standard Output ===")
            
            if command_result.log_files and command_result.log_files.stdout:
                stdout_lines, stdout_count, stdout_preview = self._read_log_file(
                    command_result.log_files.stdout
                )
                
                if stdout_count > 0:
                    # Add line count information
                    content_lines.append(f"({stdout_count} lines)")
                    
                    # Add preview lines
                    content_lines.extend(stdout_preview)
                    
                    # Add "more" message if needed
                    if stdout_count > 3:
                        content_lines.append(self.MSG_VIEW_FULL_OUTPUT)
                else:
                    content_lines.extend(stdout_preview)  # Will contain error message if any
            else:
                content_lines.append(self.MSG_NO_OUTPUT_FILE)
            
            # Add stderr content if available
            content_lines.append("")
            content_lines.append("=== Standard Error ===")
            
            if command_result.log_files and command_result.log_files.stderr:
                stderr_lines, stderr_count, stderr_preview = self._read_log_file(
                    command_result.log_files.stderr
                )
                
                if stderr_count > 0:
                    # Add line count information
                    content_lines.append(f"({stderr_count} lines)")
                    
                    # Add preview lines
                    content_lines.extend(stderr_preview)
                    
                    # Add "more" message if needed
                    if stderr_count > 3:
                        content_lines.append(self.MSG_VIEW_FULL_ERROR)
                else:
                    content_lines.extend(stderr_preview)  # Will contain error message if any
            else:
                content_lines.append(self.MSG_NO_ERROR_FILE)
            
            # Update the content widget with markup disabled
            content_widget.markup = False
            content_widget.update("\n".join(content_lines))
            
            # Reset scroll position to the top
            content_widget.scroll_home()
            
            # Force a refresh to ensure the UI updates
            self.refresh()
        except Exception as e:
            self.logger.error(f"Error updating command output: {e}")
            try:
                self.update_content("sub-pane-content", f"(Error displaying command output: {e})")
            except Exception as inner_e:
                # Minimal error handling
                self.logger.error(f"Failed to display error message: {inner_e}")
