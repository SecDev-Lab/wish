"""New Wish Main Pane widget for wish-sh TUI."""

from typing import List
from textual.app import ComposeResult
from textual.widgets import Static

from wish_sh.tui.widgets.base_pane import BasePane


class NewWishMainPane(BasePane):
    """Main content pane for new wish mode."""

    def __init__(self, *args, **kwargs):
        """Initialize the NewWishMainPane.
        
        Args:
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(*args, **kwargs)

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        yield Static("(New wish content will be displayed here)", id="main-pane-content", markup=True)
    
    def update_for_input_wish(self):
        """Update for INPUT_WISH state."""
        self.update_content("main-pane-content", "")
    
    def update_for_ask_wish_detail(self):
        """Update for ASK_WISH_DETAIL state."""
        self.update_content("main-pane-content", "[b]What's the target IP address or hostname?[/b]")
    
    def update_for_suggest_commands(self, commands: List[str]):
        """Update for SUGGEST_COMMANDS state.
        
        Args:
            commands: The commands to suggest.
        """
        content = "[b]以下のコマンドを実行しますか？[/b]\n\n"
        for i, cmd in enumerate(commands, 1):
            content += f"[{i}] {cmd}\n"
        self.update_content("main-pane-content", content)
    
    def update_for_adjust_commands(self, commands: List[str]):
        """Update for ADJUST_COMMANDS state.
        
        Args:
            commands: The commands to adjust.
        """
        content = "[b]修正内容を指定してください[/b]\n\n"
        for i, cmd in enumerate(commands, 1):
            content += f"[{i}] {cmd}\n"
        self.update_content("main-pane-content", content)
    
    def update_for_confirm_commands(self, commands: List[str]):
        """Update for CONFIRM_COMMANDS state.
        
        Args:
            commands: The commands to confirm.
        """
        content = "[b]以下のコマンドを実行します[/b]\n\n"
        for i, cmd in enumerate(commands, 1):
            content += f"[{i}] {cmd}\n"
        self.update_content("main-pane-content", content)
    
    def update_for_execute_commands(self, commands: List[str]):
        """Update for EXECUTE_COMMANDS state.
        
        Args:
            commands: The commands being executed.
        """
        content = "[b]コマンドを実行中...[/b]\n\n"
        for i, cmd in enumerate(commands, 1):
            content += f"[{i}] {cmd}\n"
        self.update_content("main-pane-content", content)
