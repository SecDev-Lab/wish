"""Help Pane widget for wish-sh TUI."""

from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Static


class HelpPane(Container):
    """Help information pane."""

    # CSS moved to external file: wish_tui.css

    # Help text definitions
    DEFAULT_HELP = 'Help: [magenta][b]←[/b][/magenta] Wish Select | [magenta][b]→[/b][/magenta] Main | [magenta][b]Ctrl+↑[/b][/magenta] Main | [magenta][b]Ctrl+↓[/b][/magenta] Sub | [magenta][b]q[/b][/magenta] Confirm Quit | [magenta][b]Ctrl+Q[/b][/magenta] Quit'
    WISH_SELECT_HELP = 'Help: [magenta][b]↑↓[/b][/magenta] Select Wish | [magenta][b]→[/b][/magenta] Main | [magenta][b]q[/b][/magenta] Confirm Quit | [magenta][b]Ctrl+Q[/b][/magenta] Quit'
    MAIN_PANE_HELP = 'Help: [magenta][b]←[/b][/magenta] Wish Select | [magenta][b]Ctrl+↓[/b][/magenta] Sub | [magenta][b]q[/b][/magenta] Confirm Quit | [magenta][b]Ctrl+Q[/b][/magenta] Quit'
    SUB_PANE_HELP = 'Help: [magenta][b]←[/b][/magenta] Wish Select | [magenta][b]Ctrl+↑[/b][/magenta] Main | [magenta][b]q[/b][/magenta] Confirm Quit | [magenta][b]Ctrl+Q[/b][/magenta] Quit'

    def __init__(self, *args, **kwargs):
        """Initialize the HelpPane."""
        super().__init__(*args, **kwargs)
        self.help_text = self.DEFAULT_HELP

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        yield Static(self.help_text, id="help-content", markup=True)
    
    def update_help(self, active_pane: str) -> None:
        """Update the help text based on the active pane.
        
        Args:
            active_pane: The ID of the active pane.
        """
        if active_pane == "wish-select":
            self.help_text = self.WISH_SELECT_HELP
        elif active_pane == "main-pane":
            self.help_text = self.MAIN_PANE_HELP
        elif active_pane == "sub-pane":
            self.help_text = self.SUB_PANE_HELP
        else:
            self.help_text = self.DEFAULT_HELP
        
        # Update the help content
        help_content = self.query_one("#help-content")
        help_content.update(self.help_text)
