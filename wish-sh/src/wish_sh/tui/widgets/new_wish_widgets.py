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
        # 実際の機能用のウィジェット
        yield ShellTerminalWidget(id="shell-terminal")

    def on_mount(self) -> None:
        """Event handler called when the widget is mounted."""
        # Ensure the shell terminal gets focus
        try:
            shell_terminal = self.query_one("#shell-terminal", ShellTerminalWidget)
            shell_terminal.focus()
            
            # 確実にフォーカスが設定されるようにタイマーを設定
            self.set_timer(0.1, self._ensure_shell_terminal_focus)
            # 定期的にフォーカスを確認するタイマーを設定
            self.set_interval(1.0, self._ensure_shell_terminal_focus)
        except Exception as e:
            logger = setup_logger("wish_sh.tui.WishInputForm")
            logger.error(f"Error focusing shell terminal: {e}")

    def on_show(self) -> None:
        """Event handler called when the widget is shown."""
        # Ensure the shell terminal gets focus when shown
        try:
            shell_terminal = self.query_one("#shell-terminal", ShellTerminalWidget)
            shell_terminal.focus()
            
            # 確実にフォーカスが設定されるようにタイマーを設定
            self.set_timer(0.1, self._ensure_shell_terminal_focus)
        except Exception as e:
            logger = setup_logger("wish_sh.tui.WishInputForm")
            logger.error(f"Error focusing shell terminal: {e}")
    
    def _ensure_shell_terminal_focus(self) -> None:
        """シェルターミナルウィジェットのフォーカスを確実に設定する"""
        try:
            shell_terminal = self.query_one("#shell-terminal", ShellTerminalWidget)
            shell_terminal.focus()
            
            # 現在のフォーカスを確認
            from textual.app import App
            app = App.get()
            if app.focused is not shell_terminal:
                # 再度フォーカスを設定
                shell_terminal.focus()
        except Exception as e:
            logger = setup_logger("wish_sh.tui.WishInputForm")
            logger.error(f"Error ensuring ShellTerminalWidget focus: {e}")
    
    def on_key(self, event) -> None:
        """キーイベントを処理する"""
        # シェルターミナルにフォーカスを設定
        try:
            shell_terminal = self.query_one("#shell-terminal", ShellTerminalWidget)
            shell_terminal.focus()
        except Exception as e:
            logger = setup_logger("wish_sh.tui.WishInputForm")
            logger.error(f"Error focusing shell terminal: {e}")
        
        # イベントを消費せず、伝播させる
        # シェルターミナルが処理できるようにする
        return False
        
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        # ボタンが削除されたため、このメソッドは使用されません
        pass

    def on_wish_input_submitted(self, event: WishInputSubmitted) -> None:
        """Handle wish input submitted event."""
        # ログ出力
        logger = setup_logger("wish_sh.tui.WishInputForm")
        
        try:
            # Forward the message to parent
            # 直接MainScreenにメッセージを送信
            from textual.app import App
            app = App.get()
            main_screen = app.screen
            
            # メッセージを送信（通常の方法と直接的な方法の両方を試す）
            self.post_message(event)
            
            # 直接スクリーンにもメッセージを送信
            if hasattr(main_screen, "on_wish_input_submitted"):
                main_screen.on_wish_input_submitted(event)
        except Exception as e:
            logger.error(f"Error forwarding WishInputSubmitted message: {e}")


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
        self.logger = setup_logger("wish_sh.tui.WishDetailForm")
        self.waiting_for_response = False

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        # シェルターミナルウィジェットを使用
        yield ShellTerminalWidget(id="shell-terminal-detail")

    def on_mount(self) -> None:
        """Event handler called when the widget is mounted."""
        try:
            # デバッグログを追加
            self.logger.debug("WishDetailForm.on_mount() called")
            
            # シェルターミナルを取得
            self.shell_terminal = self.query_one("#shell-terminal-detail", ShellTerminalWidget)
            self.logger.debug(f"Shell terminal found: {self.shell_terminal}")
            
            # 質問を表示
            message = f"{self.question}\n(e.g. 10.10.10.40, or type 'back' to return)\n> "
            self.logger.debug(f"Adding output to shell terminal: {message}")
            self.shell_terminal.add_output(message)
            
            # 入力待機状態に設定
            self.waiting_for_response = True
            
            # シェルターミナルにフォーカスを設定
            self.logger.debug("Setting focus to shell terminal")
            self.shell_terminal.focus()
            
            # 確実にフォーカスが設定されるようにタイマーを設定
            self.set_timer(0.1, self._ensure_shell_terminal_focus)
            # 定期的にフォーカスを確認するタイマーを設定
            self.set_interval(1.0, self._ensure_shell_terminal_focus)
            
            # WishInputSubmittedメッセージをハンドリング
            self.shell_terminal.on_wish_input_submitted = self.on_wish_input_submitted
            
            # 出力が表示されていることを確認
            self.logger.debug("WishDetailForm.on_mount() completed")
        except Exception as e:
            self.logger.error(f"Error in WishDetailForm.on_mount(): {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
    
    def _ensure_shell_terminal_focus(self) -> None:
        """シェルターミナルウィジェットのフォーカスを確実に設定する"""
        try:
            shell_terminal = self.query_one("#shell-terminal-detail", ShellTerminalWidget)
            shell_terminal.focus()
            
            # 現在のフォーカスを確認
            from textual.app import App
            app = App.get()
            if app.focused is not shell_terminal:
                self.logger.warning(f"Shell terminal is not focused, current focus: {app.focused}")
                # 再度フォーカスを設定
                shell_terminal.focus()
        except Exception as e:
            self.logger.error(f"Error ensuring shell terminal focus: {e}")

    def on_wish_input_submitted(self, event: WishInputSubmitted) -> None:
        """Handle wish input submitted event."""
        if not self.waiting_for_response:
            return
            
        response = event.wish_text.strip()
        self.logger.debug(f"WishDetailForm received response: {response}")
        
        if response.lower() == 'back':
            self.logger.debug("Posting CommandsRejected message")
            self.post_message(CommandsRejected())
            # メッセージが処理されるまでフラグをリセットしない
            # self.waiting_for_response = False
        elif response:
            self.logger.debug(f"Posting WishDetailSubmitted message with detail: {response}")
            self.post_message(WishDetailSubmitted(response))
            # メッセージが処理されるまでフラグをリセットしない
            # self.waiting_for_response = False
        else:
            # 空の応答の場合、再度入力を促す
            self.logger.debug("Empty response, prompting again")
            self.shell_terminal.add_output("Please enter a valid value or type 'back' to return.\n> ")



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
        self.logger = setup_logger("wish_sh.tui.CommandAdjustForm")
        self.waiting_for_response = False
        self.current_command_index = 0
        self.adjusted_commands = list(commands)  # コピーを作成
        self.skipped_commands = [False] * len(commands)  # スキップフラグ

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        # シェルターミナルウィジェットを使用
        yield ShellTerminalWidget(id="shell-terminal-adjust")

    def on_mount(self) -> None:
        """Event handler called when the widget is mounted."""
        try:
            # デバッグログを追加
            self.logger.debug("CommandAdjustForm.on_mount() called")
            
            # シェルターミナルを取得
            self.shell_terminal = self.query_one("#shell-terminal-adjust", ShellTerminalWidget)
            self.logger.debug(f"Shell terminal found: {self.shell_terminal}")
            
            # 初期メッセージを表示
            self.logger.debug("Adding initial message to shell terminal")
            self.shell_terminal.add_output("Specify which commands to execute or adjust:\n\n")
            
            # コマンドリストを表示
            self.logger.debug("Displaying command list")
            self._display_commands()
            
            # 最初のコマンドの調整を開始
            self.logger.debug("Prompting for first command")
            self._prompt_for_next_command()
            
            # 入力待機状態に設定
            self.waiting_for_response = True
            
            # シェルターミナルにフォーカスを設定
            self.logger.debug("Setting focus to shell terminal")
            self.shell_terminal.focus()
            
            # 確実にフォーカスが設定されるようにタイマーを設定
            self.set_timer(0.1, self._ensure_shell_terminal_focus)
            # 定期的にフォーカスを確認するタイマーを設定
            self.set_interval(1.0, self._ensure_shell_terminal_focus)
            
            # WishInputSubmittedメッセージをハンドリング
            self.shell_terminal.on_wish_input_submitted = self.on_wish_input_submitted
            
            # 出力が表示されていることを確認
            self.logger.debug("CommandAdjustForm.on_mount() completed")
        except Exception as e:
            self.logger.error(f"Error in CommandAdjustForm.on_mount(): {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
    
    def _ensure_shell_terminal_focus(self) -> None:
        """シェルターミナルウィジェットのフォーカスを確実に設定する"""
        try:
            shell_terminal = self.query_one("#shell-terminal-adjust", ShellTerminalWidget)
            shell_terminal.focus()
            
            # 現在のフォーカスを確認
            from textual.app import App
            app = App.get()
            if app.focused is not shell_terminal:
                self.logger.warning(f"Shell terminal is not focused, current focus: {app.focused}")
                # 再度フォーカスを設定
                shell_terminal.focus()
        except Exception as e:
            self.logger.error(f"Error ensuring shell terminal focus: {e}")

    def _display_commands(self) -> None:
        """現在のコマンドリストを表示する"""
        command_list = ""
        for i, cmd in enumerate(self.adjusted_commands, 1):
            status = "[スキップ]" if self.skipped_commands[i-1] else ""
            command_list += f"[{i}] {cmd} {status}\n"
        self.shell_terminal.add_output(f"{command_list}\n")

    def _prompt_for_next_command(self) -> None:
        """次のコマンドの調整を促す"""
        if self.current_command_index < len(self.adjusted_commands):
            cmd = self.adjusted_commands[self.current_command_index]
            self.shell_terminal.add_output(f"Command [{self.current_command_index + 1}]: {cmd}\n")
            self.shell_terminal.add_output("Enter new command (or 'skip' to skip, 'keep' to keep as is, 'done' to finish, 'cancel' to cancel):\n> ")
        else:
            # すべてのコマンドを処理した場合
            self.shell_terminal.add_output("All commands processed. Type 'done' to apply changes or 'cancel' to cancel:\n> ")

    def on_wish_input_submitted(self, event: WishInputSubmitted) -> None:
        """Handle wish input submitted event."""
        if not self.waiting_for_response:
            return
            
        response = event.wish_text.strip()
        
        if response.lower() == 'cancel':
            self.post_message(CommandAdjustCancelled())
            self.waiting_for_response = False
            return
            
        if response.lower() == 'done':
            # スキップされていないコマンドのみを含める
            final_commands = [cmd for i, cmd in enumerate(self.adjusted_commands) if not self.skipped_commands[i]]
            if final_commands:
                self.post_message(CommandsAdjusted(final_commands))
            else:
                self.shell_terminal.add_output("No commands selected. Please select at least one command or cancel.\n> ")
                return
            self.waiting_for_response = False
            return
            
        if self.current_command_index < len(self.adjusted_commands):
            if response.lower() == 'skip':
                # このコマンドをスキップ
                self.skipped_commands[self.current_command_index] = True
                self.current_command_index += 1
            elif response.lower() == 'keep':
                # このコマンドをそのまま保持
                self.current_command_index += 1
            elif response:
                # コマンドを更新
                self.adjusted_commands[self.current_command_index] = response
                self.current_command_index += 1
            
            # 更新されたコマンドリストを表示
            self.shell_terminal.add_output("\nCurrent commands:\n")
            self._display_commands()
            
            # 次のコマンドの処理へ
            self._prompt_for_next_command()
        else:
            self.shell_terminal.add_output("All commands processed. Type 'done' to apply changes or 'cancel' to cancel:\n> ")


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
        self.logger = setup_logger("wish_sh.tui.CommandConfirmForm")
        self.waiting_for_response = False

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        # シェルターミナルウィジェットを使用
        yield ShellTerminalWidget(id="shell-terminal-confirm")

    def on_mount(self) -> None:
        """Event handler called when the widget is mounted."""
        try:
            # デバッグログを追加
            self.logger.debug("CommandConfirmForm.on_mount() called")
            
            # シェルターミナルを取得
            self.shell_terminal = self.query_one("#shell-terminal-confirm", ShellTerminalWidget)
            self.logger.debug(f"Shell terminal found: {self.shell_terminal}")
            
            # コマンドリストを表示
            command_list = "\n".join([f"[{i}] {cmd}" for i, cmd in enumerate(self.commands, 1)])
            message = f"The following commands will be executed:\n\n{command_list}\n\nExecute? (y/n) > "
            self.logger.debug(f"Adding output to shell terminal: {message}")
            self.shell_terminal.add_output(message)
            
            # 入力待機状態に設定
            self.waiting_for_response = True
            
            # シェルターミナルにフォーカスを設定
            self.logger.debug("Setting focus to shell terminal")
            self.shell_terminal.focus()
            
            # 確実にフォーカスが設定されるようにタイマーを設定
            self.set_timer(0.1, self._ensure_shell_terminal_focus)
            # 定期的にフォーカスを確認するタイマーを設定
            self.set_interval(1.0, self._ensure_shell_terminal_focus)
            
            # WishInputSubmittedメッセージをハンドリング
            self.shell_terminal.on_wish_input_submitted = self.on_wish_input_submitted
            
            # 出力が表示されていることを確認
            self.logger.debug("CommandConfirmForm.on_mount() completed")
        except Exception as e:
            self.logger.error(f"Error in CommandConfirmForm.on_mount(): {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
    
    def _ensure_shell_terminal_focus(self) -> None:
        """シェルターミナルウィジェットのフォーカスを確実に設定する"""
        try:
            shell_terminal = self.query_one("#shell-terminal-confirm", ShellTerminalWidget)
            shell_terminal.focus()
            
            # 現在のフォーカスを確認
            from textual.app import App
            app = App.get()
            if app.focused is not shell_terminal:
                self.logger.warning(f"Shell terminal is not focused, current focus: {app.focused}")
                # 再度フォーカスを設定
                shell_terminal.focus()
        except Exception as e:
            self.logger.error(f"Error ensuring shell terminal focus: {e}")

    def on_wish_input_submitted(self, event: WishInputSubmitted) -> None:
        """Handle wish input submitted event."""
        if not self.waiting_for_response:
            return
            
        response = event.wish_text.lower().strip()
        self.logger.debug(f"CommandConfirmForm received response: {response}")
        
        if response in ['y', 'yes']:
            self.logger.debug("Posting ExecutionConfirmed message")
            self.post_message(ExecutionConfirmed())
            # メッセージが処理されるまでフラグをリセットしない
            # self.waiting_for_response = False
        elif response in ['n', 'no']:
            self.logger.debug("Posting ExecutionCancelled message")
            self.post_message(ExecutionCancelled())
            # メッセージが処理されるまでフラグをリセットしない
            # self.waiting_for_response = False
        else:
            # 無効な応答の場合、再度入力を促す
            self.logger.debug(f"Invalid response: {response}, prompting again")
            self.shell_terminal.add_output("Invalid response. Please enter 'y' or 'n'.\n(y/n) > ")


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
        self.logger = setup_logger("wish_sh.tui.CommandExecuteStatus")
        self.waiting_for_response = False

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        # シェルターミナルウィジェットを使用
        yield ShellTerminalWidget(id="shell-terminal-execute")

    def on_mount(self) -> None:
        """Event handler called when the widget is mounted."""
        try:
            # デバッグログを追加
            self.logger.debug("CommandExecuteStatus.on_mount() called")
            
            # シェルターミナルを取得
            self.shell_terminal = self.query_one("#shell-terminal-execute", ShellTerminalWidget)
            self.logger.debug(f"Shell terminal found: {self.shell_terminal}")
            
            # コマンドリストと実行状態を表示
            command_list = "\n".join([f"[{i}] {cmd} [🔄 Running]" for i, cmd in enumerate(self.commands, 1)])
            message = f"Executing commands:\n\n{command_list}\n\nType 'back' to return to input mode > "
            self.logger.debug(f"Adding output to shell terminal: {message}")
            self.shell_terminal.add_output(message)
            
            # 入力待機状態に設定
            self.waiting_for_response = True
            
            # シェルターミナルにフォーカスを設定
            self.logger.debug("Setting focus to shell terminal")
            self.shell_terminal.focus()
            
            # 確実にフォーカスが設定されるようにタイマーを設定
            self.set_timer(0.1, self._ensure_shell_terminal_focus)
            # 定期的にフォーカスを確認するタイマーを設定
            self.set_interval(1.0, self._ensure_shell_terminal_focus)
            
            # WishInputSubmittedメッセージをハンドリング
            self.shell_terminal.on_wish_input_submitted = self.on_wish_input_submitted
            
            # 出力が表示されていることを確認
            self.logger.debug("CommandExecuteStatus.on_mount() completed")
        except Exception as e:
            self.logger.error(f"Error in CommandExecuteStatus.on_mount(): {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
    
    def _ensure_shell_terminal_focus(self) -> None:
        """シェルターミナルウィジェットのフォーカスを確実に設定する"""
        try:
            shell_terminal = self.query_one("#shell-terminal-execute", ShellTerminalWidget)
            shell_terminal.focus()
            
            # 現在のフォーカスを確認
            from textual.app import App
            app = App.get()
            if app.focused is not shell_terminal:
                self.logger.warning(f"Shell terminal is not focused, current focus: {app.focused}")
                # 再度フォーカスを設定
                shell_terminal.focus()
        except Exception as e:
            self.logger.error(f"Error ensuring shell terminal focus: {e}")

    def on_wish_input_submitted(self, event: WishInputSubmitted) -> None:
        """Handle wish input submitted event."""
        if not self.waiting_for_response:
            return
            
        response = event.wish_text.lower().strip()
        self.logger.debug(f"CommandExecuteStatus received response: {response}")
        
        if response == 'back':
            self.logger.debug("Posting CommandAdjustCancelled message")
            self.post_message(CommandAdjustCancelled())
            # メッセージが処理されるまでフラグをリセットしない
            # self.waiting_for_response = False
        else:
            # 無効な応答の場合、再度入力を促す
            self.logger.debug(f"Invalid response: {response}, prompting again")
            self.shell_terminal.add_output("Invalid response. Type 'back' to return to input mode.\n> ")
