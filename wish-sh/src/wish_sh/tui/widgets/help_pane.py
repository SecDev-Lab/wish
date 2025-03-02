"""Help Pane widget for wish-sh TUI."""

from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Static

from wish_sh.logging import setup_logger


class HelpPane(Container):
    """Help information pane."""

    # CSS moved to external file: wish_tui.css

    def __init__(self, *args, **kwargs):
        """Initialize the HelpPane."""
        super().__init__(*args, **kwargs)
        
        # Set up logger
        self.logger = setup_logger("wish_sh.tui.HelpPane")
        
        # Initialize help text
        self.help_text = self._create_default_help()
    
    @staticmethod
    def _style_shortcut(key: str) -> str:
        """ショートカットキーをスタイリングする
        
        Args:
            key: スタイリングするショートカットキー
            
        Returns:
            スタイリングされたショートカットキー
        """
        return f"[magenta][b]{key}[/b][/magenta]"
    
    def _create_default_help(self) -> str:
        """デフォルトのヘルプテキストを作成する
        
        Returns:
            デフォルトのヘルプテキスト
        """
        return (
            f"Help: {self._style_shortcut('←/h')} Wish Select | "
            f"{self._style_shortcut('→/l')} Main | "
            f"{self._style_shortcut('Ctrl+↑/k')} Main | "
            f"{self._style_shortcut('Ctrl+↓/j')} Sub | "
            f"{self._style_shortcut('q')} Confirm Quit | "
            f"{self._style_shortcut('Ctrl+Q')} Quit"
        )
    
    def _create_wish_select_help(self) -> str:
        """Wish Select ペイン用のヘルプテキストを作成する
        
        Returns:
            Wish Select ペイン用のヘルプテキスト
        """
        return (
            f"Help: {self._style_shortcut('↑↓/k j')} Select Wish | "
            f"{self._style_shortcut('Enter/Space')} Decide & Go to Main | "
            f"{self._style_shortcut('→/l')} Main | "
            f"{self._style_shortcut('q')} Confirm Quit | "
            f"{self._style_shortcut('Ctrl+Q')} Quit"
        )
    
    def _create_main_pane_help(self) -> str:
        """Main ペイン用のヘルプテキストを作成する
        
        Returns:
            Main ペイン用のヘルプテキスト
        """
        return (
            f"Help: {self._style_shortcut('←/h')} Wish Select | "
            f"{self._style_shortcut('↑↓/k j')} Select Command | "
            f"{self._style_shortcut('Enter/Space')} Decide & Go to Sub | "
            f"{self._style_shortcut('Ctrl+↓/j')} Sub | "
            f"{self._style_shortcut('q')} Confirm Quit | "
            f"{self._style_shortcut('Ctrl+Q')} Quit"
        )
    
    def _create_sub_pane_help(self) -> str:
        """Sub ペイン用のヘルプテキストを作成する
        
        Returns:
            Sub ペイン用のヘルプテキスト
        """
        return (
            f"Help: {self._style_shortcut('←/h')} Wish Select | "
            f"{self._style_shortcut('Ctrl+↑/k')} Main | "
            f"{self._style_shortcut('j/k')} Line Down/Up | "
            f"{self._style_shortcut('o')} View Full Output | "
            f"{self._style_shortcut('e')} View Full Error | "
            f"{self._style_shortcut('q')} Confirm Quit | "
            f"{self._style_shortcut('Ctrl+Q')} Quit"
        )

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        yield Static(self.help_text, id="help-content", markup=True)
    
    def update_help(self, active_pane: str) -> None:
        """Update the help text based on the active pane.
        
        Args:
            active_pane: The ID of the active pane.
        """
        if active_pane == "wish-select":
            self.help_text = self._create_wish_select_help()
        elif active_pane == "main-pane":
            self.help_text = self._create_main_pane_help()
        elif active_pane == "sub-pane":
            self.help_text = self._create_sub_pane_help()
        else:
            self.help_text = self._create_default_help()
        
        # Update the help content
        help_content = self.query_one("#help-content")
        help_content.update(self.help_text)
