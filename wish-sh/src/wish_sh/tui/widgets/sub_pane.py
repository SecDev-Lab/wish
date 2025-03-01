"""Sub Pane widget for wish-sh TUI."""

import os
from textual.app import ComposeResult
from textual.widgets import Static
from textual.containers import Grid

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
        except:
            pass
            
        content_widget = self.query_one("#sub-pane-content")
        content_widget.update("新しいWishのコマンド出力がここに表示されます。")
    
    def update_command_output(self, command_result):
        """Update the pane with command output details.
        
        Args:
            command_result: The command result to display.
        """
        try:
            self.current_command = command_result
            
            # Get existing content widget
            try:
                content = self.query_one("#sub-pane-content")
            except:
                # Create a new content widget if it doesn't exist
                content = Static(id="sub-pane-content")
                self.mount(content)
            
            if not command_result:
                content.update("(No command selected)")
                return
            
            # Format command details as text
            content_lines = []
            
            # Add command - with label and value on the same line
            # Escape any markup in the command text
            escaped_command = command_result.command.replace("[", "\\[").replace("]", "\\]")
            content_lines.append(f"[b]Command:[/b] {escaped_command}")
            content_lines.append("")
            
            # Add stdout content if available
            if command_result.log_files and command_result.log_files.stdout:
                content_lines.append("[b]Standard Output:[/b]")
                
                try:
                    # Check if the file exists
                    if os.path.exists(command_result.log_files.stdout):
                        # Read the first few lines of stdout
                        with open(command_result.log_files.stdout, "r") as f:
                            stdout_lines = f.readlines()[:20]  # First 20 lines only
                        
                        if stdout_lines:
                            for line in stdout_lines:
                                # Escape any markup in the output
                                escaped_line = line.rstrip().replace("[", "\\[").replace("]", "\\]")
                                content_lines.append(escaped_line)
                            if len(stdout_lines) == 20:
                                content_lines.append("... (output truncated)")
                        else:
                            content_lines.append("(No output)")
                    else:
                        content_lines.append(f"(Output file not found: {command_result.log_files.stdout})")
                except Exception as e:
                    content_lines.append(f"(Error reading output: {e})")
            else:
                content_lines.append("[b]Standard Output:[/b]")
                content_lines.append("(No output file available)")
            
            # Add stderr content if available
            if command_result.log_files and command_result.log_files.stderr:
                content_lines.append("")
                content_lines.append("[b]Standard Error:[/b]")
                
                try:
                    # Check if the file exists
                    if os.path.exists(command_result.log_files.stderr):
                        # Read the first few lines of stderr
                        with open(command_result.log_files.stderr, "r") as f:
                            stderr_lines = f.readlines()[:20]  # First 20 lines only
                        
                        if stderr_lines:
                            for line in stderr_lines:
                                # Escape any markup in the error output
                                escaped_line = line.rstrip().replace("[", "\\[").replace("]", "\\]")
                                content_lines.append(escaped_line)
                            if len(stderr_lines) == 20:
                                content_lines.append("... (output truncated)")
                        else:
                            content_lines.append("(No error output)")
                    else:
                        content_lines.append(f"(Error file not found: {command_result.log_files.stderr})")
                except Exception as e:
                    content_lines.append(f"(Error reading error output: {e})")
            
            # Update the content
            content_text = "\n".join(content_lines)
            content.update(content_text)
        except Exception as e:
            self.log(f"Error updating command output: {e}")
            try:
                content_widget = self.query_one("#sub-pane-content")
                content_widget.update(f"(Error displaying command output: {e})")
            except:
                # Minimal error handling
                pass
