"""New Wish Sub Pane widget for wish-sh TUI."""

from typing import List
from textual.app import ComposeResult
from textual.widgets import Static

from wish_sh.logging import setup_logger
from wish_sh.tui.new_wish_messages import (
    CommandsAccepted,
    CommandsRejected,
    CommandAdjustRequested,
)
from wish_sh.tui.widgets.base_pane import BasePane


class NewWishSubPane(BasePane):
    """Sub content pane for new wish mode.
    
    責任: コマンド関連の表示と入力に特化
    - コマンドリストの表示
    - コマンド確認メッセージの表示
    - ユーザー入力の受付（y/n/a）
    """

    # Message constants
    MSG_NEW_WISH_MODE = "Command output for new Wish will be displayed here"

    def __init__(self, *args, **kwargs):
        """Initialize the NewWishSubPane.
        
        Args:
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(*args, **kwargs)
        self.logger = setup_logger("wish_sh.tui.NewWishSubPane")

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        yield Static(self.MSG_NEW_WISH_MODE, id="sub-pane-content")
    
    def update_for_input_wish(self):
        """Update for INPUT_WISH state."""
        # 入力状態では、コマンド関連の情報を表示（まだコマンドはない）
        self.update_content("sub-pane-content", "Wishを入力してください")
    
    def update_for_ask_wish_detail(self):
        """Update for ASK_WISH_DETAIL state."""
        # 詳細入力状態では、コマンド関連の情報を表示（まだコマンドはない）
        self.update_content("sub-pane-content", "Please enter the target IP address or hostname")
    
    def update_for_suggest_commands(self, commands: List[str] = None):
        """Update for SUGGEST_COMMANDS state.
        
        Args:
            commands: The commands to suggest.
        """
        self.logger.debug(f"update_for_suggest_commands called with commands: {commands}")
        
        # コマンド確認メッセージとコマンドリストを表示
        content = "[b]コマンドを確認してください[/b]\n\n"
        content += "以下のコマンドを実行しますか？ (y/n/a)\n\n"
        if commands:
            for i, cmd in enumerate(commands, 1):
                content += f"[{i}] {cmd}\n"
            self.logger.debug(f"Content to display: {content}")
        else:
            content += "コマンドがありません。"
            self.logger.debug("No commands to display")
        
        # 強制的に更新
        try:
            static = self.query_one("#sub-pane-content")
            if static:
                static.update(content)
                self.logger.debug("Content updated via static.update()")
            else:
                self.logger.debug("Static widget not found")
                self.update_content("sub-pane-content", content)
                self.logger.debug("Content updated via update_content()")
        except Exception as e:
            self.logger.error(f"Error updating content: {e}")
            self.update_content("sub-pane-content", content)
            self.logger.debug("Content updated via update_content() after error")
    
    def update_for_adjust_commands(self, commands: List[str] = None):
        """Update for ADJUST_COMMANDS state.
        
        Args:
            commands: The commands to adjust.
        """
        self.logger.debug(f"update_for_adjust_commands called with commands: {commands}")
        
        # コマンド修正メッセージとコマンドリストを表示
        content = "[b]コマンドを修正してください[/b]\n\n"
        if commands:
            for i, cmd in enumerate(commands, 1):
                content += f"[{i}] {cmd}\n"
            self.logger.debug(f"Content to display: {content}")
        else:
            content += "コマンドがありません。"
            self.logger.debug("No commands to display")
        
        # 強制的に更新
        try:
            static = self.query_one("#sub-pane-content")
            if static:
                static.update(content)
                self.logger.debug("Content updated via static.update()")
            else:
                self.logger.debug("Static widget not found")
                self.update_content("sub-pane-content", content)
                self.logger.debug("Content updated via update_content()")
        except Exception as e:
            self.logger.error(f"Error updating content: {e}")
            self.update_content("sub-pane-content", content)
            self.logger.debug("Content updated via update_content() after error")
    
    def update_for_confirm_commands(self, commands: List[str] = None):
        """Update for CONFIRM_COMMANDS state.
        
        Args:
            commands: The commands to confirm.
        """
        self.logger.debug(f"update_for_confirm_commands called with commands: {commands}")
        
        # コマンド確認メッセージとコマンドリストを表示
        content = "[b]以下のコマンドを実行します。よろしいですか？ (y/n)[/b]\n\n"
        if commands:
            for i, cmd in enumerate(commands, 1):
                content += f"[{i}] {cmd}\n"
            self.logger.debug(f"Content to display: {content}")
        else:
            content += "コマンドがありません。"
            self.logger.debug("No commands to display")
        
        # 強制的に更新
        try:
            static = self.query_one("#sub-pane-content")
            if static:
                static.update(content)
                self.logger.debug("Content updated via static.update()")
            else:
                self.logger.debug("Static widget not found")
                self.update_content("sub-pane-content", content)
                self.logger.debug("Content updated via update_content()")
        except Exception as e:
            self.logger.error(f"Error updating content: {e}")
            self.update_content("sub-pane-content", content)
            self.logger.debug("Content updated via update_content() after error")
    
    def update_for_execute_commands(self, commands: List[str] = None):
        """Update for EXECUTE_COMMANDS state.
        
        Args:
            commands: The commands being executed.
        """
        self.logger.debug(f"update_for_execute_commands called with commands: {commands}")
        
        # コマンド実行メッセージとコマンドリストを表示
        content = "[b]コマンドを実行中です。しばらくお待ちください。[/b]\n\n"
        if commands:
            for i, cmd in enumerate(commands, 1):
                content += f"[{i}] {cmd}\n"
            self.logger.debug(f"Content to display: {content}")
        else:
            content += "コマンドがありません。"
            self.logger.debug("No commands to display")
        
        # 強制的に更新
        try:
            static = self.query_one("#sub-pane-content")
            if static:
                static.update(content)
                self.logger.debug("Content updated via static.update()")
            else:
                self.logger.debug("Static widget not found")
                self.update_content("sub-pane-content", content)
                self.logger.debug("Content updated via update_content()")
        except Exception as e:
            self.logger.error(f"Error updating content: {e}")
            self.update_content("sub-pane-content", content)
            self.logger.debug("Content updated via update_content() after error")
    
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
    
    def on_key(self, event) -> bool:
        """Process key events.
        
        Args:
            event: The key event.
            
        Returns:
            bool: True if the event was handled, False otherwise.
        """
        self.logger.debug(f"Key event: {event.key}, focused: {self.has_focus}, "
                         f"active: {self.has_class('active-pane')}")
        
        # SUGGEST_COMMANDS状態でのキー処理
        if self.has_class('active-pane'):
            # y/n/aキーの処理
            if event.key.lower() in ('y', 'yes'):
                self.logger.debug("'y' key pressed, posting CommandsAccepted")
                self.post_message(CommandsAccepted())
                return True
            elif event.key.lower() in ('n', 'no'):
                self.logger.debug("'n' key pressed, posting CommandsRejected")
                self.post_message(CommandsRejected())
                return True
            elif event.key.lower() in ('a', 'adjust'):
                self.logger.debug("'a' key pressed, posting CommandAdjustRequested")
                self.post_message(CommandAdjustRequested())
                return True
            
            # スクロールキーの処理
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
