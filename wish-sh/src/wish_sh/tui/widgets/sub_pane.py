"""Sub Pane widget for wish-sh TUI."""

import os
from textual.app import ComposeResult
from textual.widgets import Static
from textual.containers import Horizontal

from wish_sh.tui.utils import make_markup_safe, sanitize_command_text
from wish_sh.tui.widgets.base_pane import BasePane


class SubPane(BasePane):
    """Sub content pane for displaying command output details."""

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
        yield Static("(Select a command to view details)", id="sub-pane-content")
    
    def update_for_new_wish_mode(self):
        """Update the pane for New Wish mode."""
        # Remove old grid if exists
        try:
            old_grid = self.query_one("#command-details-grid")
            self.remove(old_grid)
        except Exception as e:
            self.logger.debug(f"No command-details-grid to remove: {e}")
            
        self.update_content("sub-pane-content", "新しいWishのコマンド出力がここに表示されます。")
    
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
                return [], 0, [f"(File not found: {file_path})"]
                
            with open(file_path, "r") as f:
                lines = f.readlines()
                
            if not lines:
                return [], 0, ["(No output)"]
                
            # Get preview lines (first few lines)
            preview_lines = []
            for line in lines[:max_preview_lines]:
                safe_line = sanitize_command_text(line.rstrip())
                preview_lines.append(safe_line)
                
            return lines, len(lines), preview_lines
        except Exception as e:
            self.logger.error(f"Error reading log file: {e}")
            return [], 0, [f"(Error reading file: {e})"]
    
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
                content_widget.update("(No command selected)")
                return
            
            # Create content lines for the widget
            content_lines = []
            
            # Add command with label and value on the same line
            safe_command = sanitize_command_text(command_result.command)
            content_lines.append(f"Command: {safe_command}")
            content_lines.append("")
            
            # Add stdout content if available
            content_lines.append("Standard Output:")
            
            if command_result.log_files and command_result.log_files.stdout:
                stdout_lines, stdout_count, stdout_preview = self._read_log_file(
                    command_result.log_files.stdout
                )
                
                if stdout_count > 0:
                    # Add line count information
                    content_lines.append(f"({stdout_count} lines total)")
                    
                    # Add preview lines
                    content_lines.extend(stdout_preview)
                    
                    # Add "more" message if needed
                    if stdout_count > 3:
                        content_lines.append("... (Press 'o' to view full output)")
                else:
                    content_lines.extend(stdout_preview)  # Will contain error message if any
            else:
                content_lines.append("(No output file available)")
            
            # Add stderr content if available
            content_lines.append("")
            content_lines.append("Standard Error:")
            
            if command_result.log_files and command_result.log_files.stderr:
                stderr_lines, stderr_count, stderr_preview = self._read_log_file(
                    command_result.log_files.stderr
                )
                
                if stderr_count > 0:
                    # Add line count information
                    content_lines.append(f"({stderr_count} lines total)")
                    
                    # Add preview lines
                    content_lines.extend(stderr_preview)
                    
                    # Add "more" message if needed
                    if stderr_count > 3:
                        content_lines.append("... (Press 'e' to view full error output)")
                else:
                    content_lines.extend(stderr_preview)  # Will contain error message if any
            else:
                content_lines.append("(No error output)")
            
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
