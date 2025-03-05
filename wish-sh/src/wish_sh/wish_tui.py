import asyncio
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label, Static

from wish_models import CommandState, Wish, WishState, UtcDatetime
from wish_sh.settings import Settings
from wish_sh.wish_manager import WishManager


class WishInput(Screen):
    """Screen for inputting a wish."""

    def compose(self) -> ComposeResult:
        """Compose the wish input screen."""
        yield Header(show_clock=True)
        yield Container(
            Label("wish✨️", id="wish-prompt", markup=False),
            Input(placeholder="Enter your wish here...", id="wish-input"),
            id="wish-container",
        )
        yield Footer()

    @on(Input.Submitted)
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        wish_text = event.value.strip()
        if wish_text:
            # Create a new wish
            wish = Wish.create(wish_text)
            wish.state = WishState.DOING

            # Generate mock commands (in a real app, this would call an LLM)
            commands = [f"echo 'Executing wish: {wish_text}'", f"echo 'Processing {wish_text}' && ls -la"]

            # Switch to command suggestion screen
            self.app.push_screen(CommandSuggestion(wish, commands))


class CommandSuggestion(Screen):
    """Screen for suggesting commands."""

    def __init__(self, wish: Wish, commands: list[str]) -> None:
        """Initialize the command suggestion screen."""
        super().__init__()
        self.wish = wish
        self.commands = commands

    def compose(self) -> ComposeResult:
        """Compose the command suggestion screen."""
        yield Header(show_clock=True)
        yield Vertical(
            Label(f"Wish: {self.wish.wish}", id="wish-text", markup=False),
            Static("Do you want to execute these commands?", id="confirmation-text", markup=False),
            *(Label(f"[{i + 1}] {cmd}", id=f"command-{i + 1}", markup=False) for i, cmd in enumerate(self.commands)),
            Container(
                Button("Yes", id="yes-button", variant="success"),
                Button("No", id="no-button", variant="error"),
                id="button-container",
            ),
            id="command-container",
        )
        yield Footer()

    @on(Button.Pressed, "#yes-button")
    def on_yes_button_pressed(self) -> None:
        """Handle yes button press."""
        # Execute the commands using WishManager
        self.app.push_screen(CommandExecutionScreen(self.wish, self.commands, self.app.wish_manager))

    @on(Button.Pressed, "#no-button")
    def on_no_button_pressed(self) -> None:
        """Handle no button press."""
        # Go back to wish input screen
        self.app.pop_screen()


class CommandExecutionScreen(Screen):
    """Screen for showing command execution."""

    def __init__(self, wish: Wish, commands: list[str], wish_manager: WishManager) -> None:
        """Initialize the command execution screen."""
        super().__init__()
        self.wish = wish
        self.commands = commands
        self.wish_manager = wish_manager
        self.command_statuses: dict[int, str] = {}  # コマンド番号とステータスのマッピング
        self.all_completed = False

    def compose(self) -> ComposeResult:
        """Compose the command execution screen."""
        yield Header(show_clock=True)
        yield Vertical(
            Label(f"Wish: {self.wish.wish}", id="wish-text", markup=False),
            Static("Executing commands...", id="execution-text", markup=False),
            *(
                Vertical(
                    Label(f"[{i + 1}] {cmd}", id=f"command-{i + 1}", markup=False),
                    Static("Waiting...", id=f"command-status-{i + 1}", classes="command-status"),
                    classes="command-container",
                )
                for i, cmd in enumerate(self.commands)
            ),
            Button("Back to Wish Input", id="back-button"),
            id="execution-container",
        )
        yield Footer()

    def on_mount(self) -> None:
        """Handle screen mount event."""
        # コマンドの実行を開始
        for i, cmd in enumerate(self.commands, 1):
            self.wish_manager.execute_command(self.wish, cmd, i)

        # 定期的に実行状態を確認するタイマーを設定
        self.set_interval(0.5, self.update_command_status)

    def update_command_status(self) -> None:
        """Update the status of running commands."""
        # 実行中のコマンドのステータスを確認
        self.wish_manager.check_running_commands()

        # UIを更新
        self.update_ui()

        # すべてのコマンドが完了したかチェック
        if not self.all_completed:
            self.check_all_commands_completed()

    def update_ui(self) -> None:
        """Update the UI with current command statuses."""
        # 各コマンドの状態を表示するUIを更新
        for i, cmd in enumerate(self.commands, 1):
            result = self.wish.get_command_result_by_num(i)
            if result:
                # マークアップ文字をエスケープ
                status = f"Status: {result.state.value}"  # .valueを使用して列挙型の値を取得
                if result.exit_code is not None:
                    status += f" (exit code: {result.exit_code})"
                if result.log_summary:
                    status += f"\nSummary: {result.log_summary}"
                self.query_one(f"#command-status-{i}").update(status)

    def check_all_commands_completed(self) -> None:
        """Check if all commands have completed and update wish state."""
        # すべてのコマンドが完了したかチェック
        all_completed = True
        any_failed = False

        for result in self.wish.command_results:
            if result.state == CommandState.DOING:
                all_completed = False
                break
            if result.state != CommandState.SUCCESS:
                any_failed = True

        if all_completed:
            self.all_completed = True
            # Wishの状態を更新
            if any_failed:
                self.wish.state = WishState.FAILED
            else:
                self.wish.state = WishState.DONE

            self.wish.finished_at = UtcDatetime.now()

            # 履歴に保存
            self.wish_manager.save_wish(self.wish)

            # 実行完了メッセージを表示
            status_text = "All commands completed."
            if any_failed:
                status_text += " Some commands failed."
            self.query_one("#execution-text").update(status_text)

    @on(Button.Pressed, "#back-button")
    def on_back_button_pressed(self) -> None:
        """Handle back button press."""
        # Go back to wish input screen (pop twice to skip command suggestion)
        self.app.pop_screen()
        self.app.pop_screen()


class WishApp(App):
    """The main Wish TUI application."""

    CSS = """
    #wish-prompt {
        margin: 1 0;
        text-align: center;
        width: 100%;
        color: yellow;
        text-style: bold;
    }

    #wish-container {
        align: center middle;
        width: 80%;
        height: 10;
    }

    #wish-input {
        width: 100%;
    }

    #command-container {
        align: center middle;
        width: 80%;
    }

    #wish-text {
        margin: 1 0;
        text-align: center;
        width: 100%;
    }

    #confirmation-text {
        margin: 1 0;
        text-align: center;
        width: 100%;
        color: yellow;
    }

    #button-container {
        margin: 1 0;
        width: 100%;
        height: 3;
        align-horizontal: center;
    }

    Button {
        margin: 0 1;
    }

    #execution-container {
        align: center middle;
        width: 80%;
    }

    #execution-text {
        margin: 1 0;
        text-align: center;
        width: 100%;
        color: green;
    }

    #back-button {
        margin: 1 0;
    }

    .command-container {
        margin: 1 0;
        width: 100%;
        border: solid green;
        padding: 1;
    }

    .command-status {
        margin-left: 2;
        color: yellow;
    }
    """

    TITLE = "Wish Shell"
    SCREENS = {"wish_input": WishInput}
    BINDINGS = [("escape", "quit", "Quit")]

    def __init__(self):
        """Initialize the Wish TUI application."""
        super().__init__()
        self.settings = Settings()
        self.wish_manager = WishManager(self.settings)

    def on_mount(self) -> None:
        """Handle app mount event."""
        self.push_screen("wish_input")


def main() -> None:
    """Run the Wish TUI application."""
    app = WishApp()
    app.run()


if __name__ == "__main__":
    main()
