"""Sub Pane widget for wish-sh TUI."""

import os
from textual.app import ComposeResult
from textual.widgets import Static

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
        yield Static("Command Output", id="sub-pane-title")
        yield Static("(Select a command to view details)", id="sub-pane-content")
    
    def update_for_new_wish_mode(self):
        """Update the pane for New Wish mode."""
        try:
            # Update title
            title_widget = self.query_one("#sub-pane-title")
            title_widget.update("Sub Pane (New wish mode)")
            
            # Update content with more meaningful text
            content_widget = self.query_one("#sub-pane-content")
            content_widget.update("新しいWishのコマンド出力がここに表示されます。")
        except Exception as e:
            self.log(f"Error updating for New Wish mode: {e}")
    
    def update_command_output(self, command_result):
        """Update the pane with command output details.
        
        Args:
            command_result: The command result to display.
        """
        try:
            self.current_command = command_result
            
            if not command_result:
                content_widget = self.query_one("#sub-pane-content")
                content_widget.update("(No command selected)")
                return
            
            content_widget = self.query_one("#sub-pane-content")
            
            # Format command output details
            content_lines = [
                f"Command: {command_result.command}",
                ""
            ]
            
            # Add stdout content if available
            if command_result.log_files and command_result.log_files.stdout:
                content_lines.append("Standard Output:")
                try:
                    # Check if the file exists
                    if os.path.exists(command_result.log_files.stdout):
                        # Read the first few lines of stdout
                        with open(command_result.log_files.stdout, "r") as f:
                            stdout_lines = f.readlines()[:20]  # First 20 lines only
                        
                        if stdout_lines:
                            content_lines.extend([line.rstrip() for line in stdout_lines])
                            if len(stdout_lines) == 20:
                                content_lines.append("... (output truncated)")
                        else:
                            content_lines.append("(No output)")
                    else:
                        content_lines.append(f"(Output file not found: {command_result.log_files.stdout})")
                except Exception as e:
                    content_lines.append(f"(Error reading output: {e})")
            else:
                content_lines.append("(No output file available)")
            
            # Add stderr content if available
            if command_result.log_files and command_result.log_files.stderr:
                content_lines.append("")
                content_lines.append("Standard Error:")
                try:
                    # Check if the file exists
                    if os.path.exists(command_result.log_files.stderr):
                        # Read the first few lines of stderr
                        with open(command_result.log_files.stderr, "r") as f:
                            stderr_lines = f.readlines()[:20]  # First 20 lines only
                        
                        if stderr_lines:
                            content_lines.extend([line.rstrip() for line in stderr_lines])
                            if len(stderr_lines) == 20:
                                content_lines.append("... (output truncated)")
                        else:
                            content_lines.append("(No error output)")
                    else:
                        content_lines.append(f"(Error file not found: {command_result.log_files.stderr})")
                except Exception as e:
                    content_lines.append(f"(Error reading error output: {e})")
            
            content_text = "\n".join(content_lines)
            content_widget.update(content_text)
        except Exception as e:
            self.log(f"Error updating command output: {e}")
            try:
                content_widget = self.query_one("#sub-pane-content")
                content_widget.update(f"(Error displaying command output: {e})")
            except:
                # Minimal error handling
                pass
