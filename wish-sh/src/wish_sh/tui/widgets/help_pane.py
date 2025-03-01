"""Help Pane widget for wish-sh TUI."""

from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Static


class HelpPane(Container):
    """Help information pane."""

    DEFAULT_CSS = """
    HelpPane {
        width: 100%;
        height: 3;
        dock: bottom;
        border: solid $primary;
        background: $surface-darken-1;
        padding: 0 1;
    }
    """

    # ヘルプテキスト定義
    DEFAULT_HELP = "Help: ← Wish Select | → Main | Ctrl+↑ Main | Ctrl+↓ Sub | q 確認して終了 | Ctrl+Q 直接終了"
    WISH_SELECT_HELP = "Help: ↑↓ Wish選択 | → Main | q 確認して終了 | Ctrl+Q 直接終了"
    MAIN_PANE_HELP = "Help: ← Wish Select | Ctrl+↓ Sub | q 確認して終了 | Ctrl+Q 直接終了"
    SUB_PANE_HELP = "Help: ← Wish Select | Ctrl+↑ Main | q 確認して終了 | Ctrl+Q 直接終了"

    def __init__(self, *args, **kwargs):
        """Initialize the HelpPane."""
        super().__init__(*args, **kwargs)
        self.help_text = self.DEFAULT_HELP

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        yield Static(self.help_text, id="help-content")
    
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
