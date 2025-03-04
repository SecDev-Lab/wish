"""New Wish Main Pane widget for wish-sh TUI."""

from typing import List, Optional
from textual.app import ComposeResult
from textual.widgets import Static

from wish_sh.logging import setup_logger
from wish_sh.tui.widgets.base_pane import BasePane


class NewWishMainPane(BasePane):
    """Main content pane for new wish mode.
    
    責任: wishの内容表示に特化
    - wishの入力と表示
    - 状態に関わらずwishの内容を保持
    - 読み取り専用の情報表示
    """

    def __init__(self, *args, **kwargs):
        """Initialize the NewWishMainPane.
        
        Args:
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(*args, **kwargs)
        self.logger = setup_logger("wish_sh.tui.NewWishMainPane")
        self.current_wish_text: Optional[str] = None

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        yield Static("(New wish content will be displayed here)", id="main-pane-content", markup=True)
    
    def update_for_input_wish(self):
        """Update for INPUT_WISH state."""
        # 入力状態では空の内容を表示（WishInputFormがマウントされるため）
        self.update_content("main-pane-content", "")
        # 現在のwish内容をクリア
        self.current_wish_text = None
    
    def update_for_ask_wish_detail(self):
        """Update for ASK_WISH_DETAIL state."""
        # wishの詳細入力に関するメッセージを表示
        if self.current_wish_text:
            content = f"[b]Wish:[/b] {self.current_wish_text}\n\n"
            content += "[b]詳細情報を入力してください[/b]\n"
            content += "What's the target IP address or hostname?"
            self.update_content("main-pane-content", content)
        else:
            self.update_content("main-pane-content", "[b]詳細情報を入力してください[/b]\n"
                                                    "What's the target IP address or hostname?")
    
    def update_for_suggest_commands(self, commands: List[str] = None):
        """Update for SUGGEST_COMMANDS state.
        
        Args:
            commands: The commands to suggest.
        """
        # wishの内容を表示（保持）
        if self.current_wish_text:
            content = f"[b]Wish:[/b] {self.current_wish_text}"
            self.update_content("main-pane-content", content)
            self.logger.debug(f"Displaying wish content: {content}")
        else:
            self.logger.debug("No wish content to display")
    
    def update_for_adjust_commands(self, commands: List[str] = None):
        """Update for ADJUST_COMMANDS state.
        
        Args:
            commands: The commands to adjust.
        """
        # wishの内容を表示（保持）
        if self.current_wish_text:
            content = f"[b]Wish:[/b] {self.current_wish_text}\n\n"
            content += "[b]コマンドを修正してください[/b]"
            content += "\nコマンドリストはSub Paneで確認できます"
            self.update_content("main-pane-content", content)
        else:
            content = "[b]コマンドを修正してください[/b]"
            content += "\nコマンドリストはSub Paneで確認できます"
            self.update_content("main-pane-content", content)
    
    def update_for_confirm_commands(self, commands: List[str] = None):
        """Update for CONFIRM_COMMANDS state.
        
        Args:
            commands: The commands to confirm.
        """
        # wishの内容を表示（保持）
        if self.current_wish_text:
            content = f"[b]Wish:[/b] {self.current_wish_text}\n\n"
            content += "[b]コマンドの実行を確認してください[/b]"
            content += "\nコマンドリストはSub Paneで確認できます"
            self.update_content("main-pane-content", content)
        else:
            content = "[b]コマンドの実行を確認してください[/b]"
            content += "\nコマンドリストはSub Paneで確認できます"
            self.update_content("main-pane-content", content)
    
    def update_for_execute_commands(self, commands: List[str] = None):
        """Update for EXECUTE_COMMANDS state.
        
        Args:
            commands: The commands being executed.
        """
        # wishの内容を表示（保持）
        if self.current_wish_text:
            content = f"[b]Wish:[/b] {self.current_wish_text}\n\n"
            content += "[b]コマンドを実行中...[/b]"
            content += "\n実行中のコマンドはSub Paneで確認できます"
            self.update_content("main-pane-content", content)
        else:
            content = "[b]コマンドを実行中...[/b]"
            content += "\n実行中のコマンドはSub Paneで確認できます"
            self.update_content("main-pane-content", content)
    
    def set_wish_text(self, wish_text: str):
        """Set the current wish text.
        
        Args:
            wish_text: The wish text to set.
        """
        self.current_wish_text = wish_text
        self.logger.debug(f"Set wish text: {wish_text}")
