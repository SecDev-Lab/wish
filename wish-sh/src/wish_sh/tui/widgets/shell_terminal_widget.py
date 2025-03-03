"""Shell Terminal Widget for wish-sh TUI."""

from typing import List, Optional

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Input, Static, RichLog
from textual.reactive import reactive

from wish_sh.tui.new_wish_messages import WishInputSubmitted
from wish_sh.logging import setup_logger


class ShellTerminalWidget(Static):
    """A terminal-like widget that emulates a shell experience."""
    
    def __init__(self, prompt: str = "wish✨️ ", *args, **kwargs):
        """Initialize the widget.
        
        Args:
            prompt: The prompt to display before input.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(*args, **kwargs)
        self.prompt = prompt
        self.command_history: List[str] = []
        self.command_history_index = -1
        self.logger = setup_logger("wish_sh.tui.ShellTerminalWidget")
    
    def compose(self) -> ComposeResult:
        """Compose the widget."""
        # Create a vertical layout
        with Vertical():
            # Output area for command history and results
            yield RichLog(id="terminal-output", wrap=False, highlight=True, markup=False)
            # Input area with prompt
            yield Input(placeholder=f"{self.prompt}", id="terminal-input")
    
    def on_mount(self) -> None:
        """Event handler called when the widget is mounted."""
        # Get references to child widgets
        self.output = self.query_one("#terminal-output", RichLog)
        self.input = self.query_one("#terminal-input", Input)
        
        # Set initial focus to input
        self.input.focus()
        
        # Set the prompt
        self.input.placeholder = self.prompt
        
        self.logger.debug("ShellTerminalWidget mounted and focused")
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submitted event."""
        # Get the input text
        command = event.value
        
        if not command.strip():
            # Don't submit empty input
            self.input.value = ""
            return
        
        # Echo the command to the output
        self.output.write(f"{self.prompt}{command}")
        
        # Add to command history
        if command not in self.command_history:
            self.command_history.append(command)
        self.command_history_index = -1
        
        # Post message with input
        self.post_message(WishInputSubmitted(command))
        
        # Clear input and refocus
        self.input.value = ""
        self.input.focus()
        
        self.logger.debug(f"Input submitted: {command}")
    
    def on_key(self, event) -> None:
        """Handle key events for command history navigation."""
        # Only handle up/down keys for command history
        if event.key == "up" and self.input.has_focus:
            # Navigate command history (previous)
            if self.command_history and self.command_history_index < len(self.command_history) - 1:
                if self.command_history_index == -1:
                    # Save current input if we're starting to navigate history
                    self.saved_input = self.input.value
                
                self.command_history_index += 1
                self.input.value = self.command_history[-(self.command_history_index + 1)]
                # Move cursor to end
                self.input.action_end()
                
                # Prevent default handling
                event.prevent_default()
                event.stop()
                
        elif event.key == "down" and self.input.has_focus:
            # Navigate command history (next)
            if self.command_history_index > -1:
                self.command_history_index -= 1
                if self.command_history_index == -1:
                    # Restore saved input when we reach the end of history
                    self.input.value = getattr(self, 'saved_input', '')
                else:
                    self.input.value = self.command_history[-(self.command_history_index + 1)]
                # Move cursor to end
                self.input.action_end()
                
                # Prevent default handling
                event.prevent_default()
                event.stop()
    
    def add_output(self, output: str) -> None:
        """Add output text to the terminal.
        
        Args:
            output: The output text to add.
        """
        if output:
            # Add output to the RichLog
            for line in output.rstrip().split("\n"):
                self.output.write(line)
            
            self.logger.debug(f"Output added: {output[:50]}{'...' if len(output) > 50 else ''}")
    
    def clear_terminal(self) -> None:
        """Clear the terminal history."""
        self.output.clear()
