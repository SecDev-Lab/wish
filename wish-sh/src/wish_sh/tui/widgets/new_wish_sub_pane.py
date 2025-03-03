"""New Wish Sub Pane widget for wish-sh TUI."""

from textual.app import ComposeResult
from textual.widgets import Static

from wish_sh.tui.widgets.base_pane import BasePane


class NewWishSubPane(BasePane):
    """Sub content pane for new wish mode."""

    # Message constants
    MSG_NEW_WISH_MODE = "Command output for new Wish will be displayed here"

    def __init__(self, *args, **kwargs):
        """Initialize the NewWishSubPane.
        
        Args:
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(*args, **kwargs)

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        yield Static(self.MSG_NEW_WISH_MODE, id="sub-pane-content")
    
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
