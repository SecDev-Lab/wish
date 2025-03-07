import asyncio
from typing import Optional

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label, Static
from wish_models import Wish, WishState
from wish_models.command_result.command_state import CommandState

from wish_sh.settings import Settings
from wish_sh.tui.widgets import UIUpdater
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

            # Generate commands using WishManager
            commands, error = self.app.wish_manager.generate_commands(wish_text)

            # Switch to command suggestion screen
            self.app.push_screen(CommandSuggestion(wish, commands, error))


class CommandSuggestion(Screen):
    """Screen for suggesting commands."""

    def __init__(self, wish: Wish, commands: list[str], error: Optional[str] = None) -> None:
        """Initialize the command suggestion screen."""
        super().__init__()
        self.wish = wish
        self.commands = commands
        self.error = error

    def compose(self) -> ComposeResult:
        """Compose the command suggestion screen."""
        yield Header(show_clock=True)

        if self.error:
            # Display error message
            yield Vertical(
                Label(f"Wish: {self.wish.wish}", id="wish-text", markup=False),
                Static(f"Error: {self.error}", id="error-text", markup=False),
                Container(
                    Button("Back to Wish Input", id="back-button"),
                    id="button-container",
                ),
                id="error-container",
            )
        else:
            # Display command suggestions
            yield Vertical(
                Label(f"Wish: {self.wish.wish}", id="wish-text", markup=False),
                Static("Do you want to execute these commands?", id="confirmation-text", markup=False),
                *(
                    Label(f"[{i + 1}] {cmd}", id=f"command-{i + 1}", markup=False)
                    for i, cmd in enumerate(self.commands)
                ),
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

    @on(Button.Pressed, "#back-button")
    def on_back_button_pressed(self) -> None:
        """Handle back button press."""
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
        self.command_statuses: dict[int, str] = {}  # Mapping of command numbers to statuses
        self.all_completed = False
        self.api_error_detected = False  # Flag to track API errors

        # Initialize command execution components
        self.executor = wish_manager.executor
        self.tracker = wish_manager.tracker
        self.ui_updater = UIUpdater(self)

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
            Container(
                Button("Back to Wish Input", id="back-button"),
                Button("Retry Analysis", id="retry-button", variant="primary", disabled=True),
                id="button-container",
            ),
            id="execution-container",
        )
        yield Footer()

    def on_mount(self) -> None:
        """Handle screen mount event."""
        # Start command execution
        self.executor.execute_commands(self.wish, self.commands)

        # Asynchronously monitor command status
        asyncio.create_task(self.monitor_commands())

    async def monitor_commands(self) -> None:
        """Asynchronously monitor command execution status."""
        while not self.all_completed:
            # Check status of running commands
            self.tracker.check_status(self.wish)

            # Analyze logs for completed commands that don't have log_summary yet
            for cmd_result in self.wish.command_results:
                if cmd_result.finished_at and not cmd_result.log_summary:
                    # Analyze the command result
                    analyzed_result = self.wish_manager.analyze_log(cmd_result)

                    # Check if API error occurred
                    if analyzed_result.state and analyzed_result.state == CommandState.API_ERROR:
                        self.api_error_detected = True
                        # Enable retry button
                        retry_button = self.query_one("#retry-button")
                        retry_button.disabled = False

                    # Update the command result in the wish object
                    for i, result in enumerate(self.wish.command_results):
                        if result.num == cmd_result.num:
                            self.wish.command_results[i] = analyzed_result
                            break

            # Update UI
            self.ui_updater.update_command_status(self.wish)

            # Check if all commands have completed
            if not self.all_completed:
                self.check_all_commands_completed()

            await asyncio.sleep(0.5)

    def check_all_commands_completed(self) -> None:
        """Check if all commands have completed and update wish state."""
        # Check if all commands have completed
        all_completed, any_failed = self.tracker.is_all_completed(self.wish)

        if all_completed:
            # Update wish state
            self.tracker.update_wish_state(self.wish)
            self.all_completed = True

            # Display completion message
            completion_message = self.tracker.get_completion_message(self.wish)

            # Add API error message if needed
            if self.api_error_detected:
                completion_message += "\nAPI error detected. Please check your internet connection and API key."

            self.ui_updater.show_completion_message(completion_message)

    @on(Button.Pressed, "#back-button")
    def on_back_button_pressed(self) -> None:
        """Handle back button press."""
        # Go back to wish input screen (pop twice to skip command suggestion)
        self.app.pop_screen()
        self.app.pop_screen()

    @on(Button.Pressed, "#retry-button")
    def on_retry_button_pressed(self) -> None:
        """Handle retry button press."""
        # Reset API error flag
        self.api_error_detected = False

        # Disable retry button
        retry_button = self.query_one("#retry-button")
        retry_button.disabled = True

        # Retry analysis for commands with API errors
        for cmd_result in self.wish.command_results:
            if cmd_result.state == CommandState.API_ERROR:
                # Reset the state to allow re-analysis
                cmd_result.state = CommandState.DOING
                cmd_result.log_summary = None

        # Update UI to show "Retrying..." status
        for _i, cmd_result in enumerate(self.wish.command_results):
            if cmd_result.state == CommandState.DOING:
                status_widget = self.query_one(f"#command-status-{cmd_result.num}")
                status_widget.update("Retrying analysis...")

        # Update execution text
        execution_text = self.query_one("#execution-text")
        execution_text.update("Retrying analysis...")


class WishApp(App):
    """The main Wish TUI application."""

    CSS_PATH = "tui/styles/app.css"

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
