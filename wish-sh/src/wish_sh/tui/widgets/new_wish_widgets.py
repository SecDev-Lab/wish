"""Widgets for New Wish mode in TUI."""

from typing import List

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Input, Label, Static, Checkbox

from wish_sh.logging import setup_logger
from wish_sh.tui.new_wish_messages import (
    WishInputSubmitted,
    WishDetailSubmitted,
    CommandsAccepted,
    CommandsRejected,
    CommandAdjustRequested,
    CommandsAdjusted,
    CommandAdjustCancelled,
    ExecutionConfirmed,
    ExecutionCancelled,
)


from wish_sh.tui.widgets.shell_terminal_widget import ShellTerminalWidget


class WishInputForm(Static):
    """Form for inputting a wish."""
    
    # キーイベントを子ウィジェットに渡すためのフラグ
    BINDINGS = []
    
    def compose(self) -> ComposeResult:
        """Compose the widget."""
        yield ShellTerminalWidget(id="shell-terminal")

    def on_mount(self) -> None:
        """Event handler called when the widget is mounted."""
        # Ensure the shell terminal gets focus
        shell_terminal = self.query_one("#shell-terminal", ShellTerminalWidget)
        shell_terminal.focus()
        
        # 確実にフォーカスが設定されるようにタイマーを設定
        self.set_timer(0.1, self._ensure_shell_terminal_focus)
        # 定期的にフォーカスを確認するタイマーを設定
        self.set_interval(1.0, self._ensure_shell_terminal_focus)
        
        # ログ出力
        logger = setup_logger("wish_sh.tui.WishInputForm")
        logger.debug("WishInputForm mounted, focusing ShellTerminalWidget")

    def on_show(self) -> None:
        """Event handler called when the widget is shown."""
        # Ensure the shell terminal gets focus when shown
        shell_terminal = self.query_one("#shell-terminal", ShellTerminalWidget)
        shell_terminal.focus()
        
        # 確実にフォーカスが設定されるようにタイマーを設定
        self.set_timer(0.1, self._ensure_shell_terminal_focus)
        
        # ログ出力
        logger = setup_logger("wish_sh.tui.WishInputForm")
        logger.debug("WishInputForm shown, focusing ShellTerminalWidget")
    
    def _ensure_shell_terminal_focus(self) -> None:
        """シェルターミナルウィジェットのフォーカスを確実に設定する"""
        try:
            shell_terminal = self.query_one("#shell-terminal", ShellTerminalWidget)
            shell_terminal.focus()
            
            # ログ出力
            logger = setup_logger("wish_sh.tui.WishInputForm")
            logger.debug("Ensuring ShellTerminalWidget focus")
            
            # 現在のフォーカスを確認
            from textual.app import App
            app = App.get()
            if app.focused is not shell_terminal:
                logger.warning(f"ShellTerminalWidget is not focused, current focus: {app.focused}")
                # 再度フォーカスを設定
                shell_terminal.focus()
        except Exception as e:
            logger = setup_logger("wish_sh.tui.WishInputForm")
            logger.error(f"Error ensuring ShellTerminalWidget focus: {e}")
    
    def on_key(self, event) -> None:
        """キーイベントを処理する"""
        # 全てのキーイベントをシェルターミナルに転送
        logger = setup_logger("wish_sh.tui.WishInputForm")
        logger.debug(f"WishInputForm received key event: {event.key}, forwarding to ShellTerminalWidget")
        
        # シェルターミナルにフォーカスを設定
        shell_terminal = self.query_one("#shell-terminal", ShellTerminalWidget)
        shell_terminal.focus()
        
        # イベントを消費せず、伝播させる
        # シェルターミナルが処理できるようにする
        return False

    def on_wish_input_submitted(self, event: WishInputSubmitted) -> None:
        """Handle wish input submitted event."""
        # Forward the message to parent
        self.post_message(event)


class WishDetailForm(Static):
    """Form for inputting wish details."""

    def __init__(self, question: str = "What's the target IP address or hostname?", *args, **kwargs):
        """Initialize the widget.
        
        Args:
            question: The question to display.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(*args, **kwargs)
        self.question = question

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        yield Label(self.question, id="wish-detail-label")
        yield Input(placeholder="e.g. 10.10.10.40", id="wish-detail-field")
        
        with Horizontal(id="wish-detail-buttons"):
            yield Button("Submit", id="wish-detail-submit-button", variant="primary")
            yield Button("Back", id="wish-detail-back-button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "wish-detail-submit-button":
            detail = self.query_one("#wish-detail-field").value
            if detail:
                self.post_message(WishDetailSubmitted(detail))
        elif event.button.id == "wish-detail-back-button":
            # Post a message to go back to the input state
            self.post_message(CommandsRejected())


class CommandSuggestForm(Static):
    """Form for suggesting commands."""

    def __init__(self, commands: List[str], *args, **kwargs):
        """Initialize the widget.
        
        Args:
            commands: The commands to suggest.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(*args, **kwargs)
        self.commands = commands

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        yield Label("Do you want to execute these commands?", id="command-suggest-label")
        
        with Vertical(id="command-list"):
            for i, cmd in enumerate(self.commands, 1):
                yield Static(f"[{i}] {cmd}", id=f"command-{i}", markup=False)
        
        with Horizontal(id="command-suggest-buttons"):
            yield Button("Yes", id="command-yes-button", variant="primary")
            yield Button("No", id="command-no-button")
            yield Button("Adjust", id="command-adjust-button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "command-yes-button":
            self.post_message(CommandsAccepted())
        elif event.button.id == "command-no-button":
            self.post_message(CommandsRejected())
        elif event.button.id == "command-adjust-button":
            self.post_message(CommandAdjustRequested())


class CommandAdjustForm(Static):
    """Form for adjusting commands."""

    def __init__(self, commands: List[str], *args, **kwargs):
        """Initialize the widget.
        
        Args:
            commands: The commands to adjust.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(*args, **kwargs)
        self.commands = commands
        self.command_inputs = []

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        yield Label("Specify which commands to execute or adjust:", id="command-adjust-label")
        
        with Vertical(id="command-adjust-list"):
            for i, cmd in enumerate(self.commands, 1):
                with Horizontal(id=f"command-row-{i}"):
                    yield Checkbox(value=True, id=f"command-check-{i}")
                    yield Input(value=cmd, id=f"command-input-{i}")
                    self.command_inputs.append(f"command-input-{i}")
        
        with Horizontal(id="command-adjust-buttons"):
            yield Button("Apply", id="command-apply-button", variant="primary")
            yield Button("Cancel", id="command-cancel-button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "command-apply-button":
            adjusted_commands = []
            for i, input_id in enumerate(self.command_inputs, 1):
                checkbox = self.query_one(f"#command-check-{i}")
                input_field = self.query_one(f"#{input_id}")
                if checkbox.value:
                    adjusted_commands.append(input_field.value)
            
            if adjusted_commands:
                self.post_message(CommandsAdjusted(adjusted_commands))
        elif event.button.id == "command-cancel-button":
            self.post_message(CommandAdjustCancelled())


class CommandConfirmForm(Static):
    """Form for confirming command execution."""

    def __init__(self, commands: List[str], *args, **kwargs):
        """Initialize the widget.
        
        Args:
            commands: The commands to confirm.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(*args, **kwargs)
        self.commands = commands

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        yield Label("The following commands will be executed:", id="command-confirm-label")
        
        with Vertical(id="command-confirm-list"):
            for i, cmd in enumerate(self.commands, 1):
                yield Static(f"[{i}] {cmd}", id=f"command-confirm-{i}", markup=False)
        
        with Horizontal(id="command-confirm-buttons"):
            yield Button("Execute", id="command-execute-button", variant="primary")
            yield Button("Cancel", id="command-cancel-button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "command-execute-button":
            self.post_message(ExecutionConfirmed())
        elif event.button.id == "command-cancel-button":
            self.post_message(ExecutionCancelled())


class CommandExecuteStatus(Static):
    """Widget for displaying command execution status."""

    def __init__(self, commands: List[str], *args, **kwargs):
        """Initialize the widget.
        
        Args:
            commands: The commands being executed.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(*args, **kwargs)
        self.commands = commands

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        yield Label("Executing commands:", id="command-execute-label")
        
        with Vertical(id="command-execute-list"):
            for i, cmd in enumerate(self.commands, 1):
                yield Static(f"[{i}] {cmd} [🔄 Running]", id=f"command-execute-{i}", markup=False)
        
        with Horizontal(id="command-execute-buttons"):
            yield Button("Back to Input", id="command-back-button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "command-back-button":
            self.post_message(CommandsRejected())  # Use this to go back to input state
