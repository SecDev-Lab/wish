"""New Wish Sub Pane widget for wish-sh TUI."""

from typing import List
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
        self.update_content("sub-pane-content", "Wishを入力してください")
    
    def update_for_ask_wish_detail(self):
        """Update for ASK_WISH_DETAIL state."""
        self.update_content("sub-pane-content", "Please enter the target IP address or hostname.")
    
    def update_for_suggest_commands(self, commands: List[str] = None):
        """Update for SUGGEST_COMMANDS state.
        
        Args:
            commands: The commands to suggest.
        """
        # ログ出力を追加
        from wish_sh.logging import setup_logger
        logger = setup_logger("wish_sh.tui.NewWishSubPane")
        logger.debug(f"update_for_suggest_commands called with commands: {commands}")
        
        content = "以下のコマンドを実行しますか？ (y/n/a)\n\n"
        if commands:
            for i, cmd in enumerate(commands, 1):
                content += f"[{i}] {cmd}\n"
            logger.debug(f"Content to display: {content}")
        else:
            content += "コマンドがありません。"
            logger.debug("No commands to display")
        
        # 強制的に更新
        try:
            static = self.query_one("#sub-pane-content")
            if static:
                static.update(content)
                logger.debug("Content updated via static.update()")
            else:
                logger.debug("Static widget not found")
                self.update_content("sub-pane-content", content)
                logger.debug("Content updated via update_content()")
        except Exception as e:
            logger.error(f"Error updating content: {e}")
            self.update_content("sub-pane-content", content)
            logger.debug("Content updated via update_content() after error")
    
    def update_for_adjust_commands(self, commands: List[str] = None):
        """Update for ADJUST_COMMANDS state.
        
        Args:
            commands: The commands to adjust.
        """
        # ログ出力を追加
        from wish_sh.logging import setup_logger
        logger = setup_logger("wish_sh.tui.NewWishSubPane")
        logger.debug(f"update_for_adjust_commands called with commands: {commands}")
        
        content = "コマンドを修正してください。\n\n"
        if commands:
            for i, cmd in enumerate(commands, 1):
                content += f"[{i}] {cmd}\n"
            logger.debug(f"Content to display: {content}")
        else:
            content += "コマンドがありません。"
            logger.debug("No commands to display")
        
        # 強制的に更新
        try:
            static = self.query_one("#sub-pane-content")
            if static:
                static.update(content)
                logger.debug("Content updated via static.update()")
            else:
                logger.debug("Static widget not found")
                self.update_content("sub-pane-content", content)
                logger.debug("Content updated via update_content()")
        except Exception as e:
            logger.error(f"Error updating content: {e}")
            self.update_content("sub-pane-content", content)
            logger.debug("Content updated via update_content() after error")
    
    def update_for_confirm_commands(self, commands: List[str] = None):
        """Update for CONFIRM_COMMANDS state.
        
        Args:
            commands: The commands to confirm.
        """
        # ログ出力を追加
        from wish_sh.logging import setup_logger
        logger = setup_logger("wish_sh.tui.NewWishSubPane")
        logger.debug(f"update_for_confirm_commands called with commands: {commands}")
        
        content = "以下のコマンドを実行します。よろしいですか？ (y/n)\n\n"
        if commands:
            for i, cmd in enumerate(commands, 1):
                content += f"[{i}] {cmd}\n"
            logger.debug(f"Content to display: {content}")
        else:
            content += "コマンドがありません。"
            logger.debug("No commands to display")
        
        # 強制的に更新
        try:
            static = self.query_one("#sub-pane-content")
            if static:
                static.update(content)
                logger.debug("Content updated via static.update()")
            else:
                logger.debug("Static widget not found")
                self.update_content("sub-pane-content", content)
                logger.debug("Content updated via update_content()")
        except Exception as e:
            logger.error(f"Error updating content: {e}")
            self.update_content("sub-pane-content", content)
            logger.debug("Content updated via update_content() after error")
    
    def update_for_execute_commands(self, commands: List[str] = None):
        """Update for EXECUTE_COMMANDS state.
        
        Args:
            commands: The commands being executed.
        """
        # ログ出力を追加
        from wish_sh.logging import setup_logger
        logger = setup_logger("wish_sh.tui.NewWishSubPane")
        logger.debug(f"update_for_execute_commands called with commands: {commands}")
        
        content = "コマンドを実行中です。しばらくお待ちください。\n\n"
        if commands:
            for i, cmd in enumerate(commands, 1):
                content += f"[{i}] {cmd}\n"
            logger.debug(f"Content to display: {content}")
        else:
            content += "コマンドがありません。"
            logger.debug("No commands to display")
        
        # 強制的に更新
        try:
            static = self.query_one("#sub-pane-content")
            if static:
                static.update(content)
                logger.debug("Content updated via static.update()")
            else:
                logger.debug("Static widget not found")
                self.update_content("sub-pane-content", content)
                logger.debug("Content updated via update_content()")
        except Exception as e:
            logger.error(f"Error updating content: {e}")
            self.update_content("sub-pane-content", content)
            logger.debug("Content updated via update_content() after error")
