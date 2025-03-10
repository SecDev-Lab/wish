import asyncio
from typing import Optional

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.screen import ModalScreen, Screen
from textual.widgets import Button, Footer, Header, Input, Label, Static
from wish_command_generation.exceptions import CommandGenerationError
from wish_models import Settings, Wish, WishState
from wish_models.command_result.command_state import CommandState
from wish_models.system_info import SystemInfo

from wish_sh.system_info_display import display_system_info
from wish_sh.tui.widgets import UIUpdater
from wish_sh.wish_manager import WishManager


class ErrorModal(ModalScreen):
    """Modal screen for displaying error messages."""

    def __init__(self, error_message: str, api_response: str = None):
        """Initialize the error modal.

        Args:
            error_message: The error message to display
            api_response: The API response that caused the error (if available)
        """
        super().__init__()
        self.error_message = error_message
        self.api_response = api_response

    def compose(self) -> ComposeResult:
        """Compose the modal screen."""
        # Create a container for the modal content
        content = [
            Label("Error", id="modal-title"),
            Static(self.error_message, id="error-info", markup=False),
        ]

        # Add command-generation response if available
        if self.api_response:
            content.append(Label("Command Generation Response:", id="command-generation-response-label"))
            content.append(Static(self.api_response, id="command-generation-response", markup=False))

        content.append(Button("Close", id="close-button", variant="primary"))

        yield Container(*content, id="modal-container")

    @on(Button.Pressed, "#close-button")
    def on_close_button_pressed(self) -> None:
        """Handle close button press."""
        self.app.pop_screen()


class SystemInfoModal(ModalScreen):
    """Modal screen for displaying basic system information."""

    def __init__(self, system_info):
        """Initialize the system info modal.

        Args:
            system_info: The system information to display
        """
        super().__init__()
        self.system_info = system_info

    def compose(self) -> ComposeResult:
        """Compose the modal screen."""
        # Create a container for the modal content
        yield Container(
            Label("System Information", id="modal-title"),
            Static(self._format_basic_info(), id="basic-info", markup=False),
            Button("Close", id="close-button", variant="primary"),
            id="modal-container",
        )

    def _format_basic_info(self) -> str:
        """Format basic system information for display."""
        # Format basic information without markup
        info = self.system_info
        lines = [
            f"OS: {info.os}",
            f"Architecture: {info.arch}",
        ]
        if info.version:
            lines.append(f"Version: {info.version}")
        lines.extend(
            [
                f"Hostname: {info.hostname}",
                f"Username: {info.username}",
            ]
        )
        if info.uid:
            lines.append(f"UID: {info.uid}")
        if info.gid:
            lines.append(f"GID: {info.gid}")
        if info.pid:
            lines.append(f"PID: {info.pid}")

        return "\n".join(lines)

    @on(Button.Pressed, "#close-button")
    def on_close_button_pressed(self) -> None:
        """Handle close button press."""
        self.app.pop_screen()


class ExecutablesModal(ModalScreen):
    """Modal screen for displaying executables information."""

    def __init__(self, executables):
        """Initialize the executables modal.

        Args:
            executables: The executables collection to display
        """
        super().__init__()
        self.executables = executables

    def compose(self) -> ComposeResult:
        """Compose the modal screen."""
        # Create a container for the modal content
        yield Container(
            Label("Executables", id="modal-title"),
            Static(self._format_executables(), id="executables-info", markup=False),
            Button("Close", id="close-button", variant="primary"),
            id="modal-container",
        )

    def _format_executables(self) -> str:
        """Format executable information for display."""
        # Format executable information without markup
        lines = [f"Executables ({len(self.executables.executables)} files)"]

        # Group executables by directory
        grouped = self.executables.group_by_directory()

        # Add directories and files
        for directory in sorted(grouped.keys()):
            lines.append(f"\n{directory} ({len(grouped[directory])} files)")

            # Add files in this directory
            for exe in sorted(grouped[directory], key=lambda x: x.filename)[:10]:  # Limit to 10 files per directory
                if exe.permissions:
                    lines.append(f"  {exe.filename} ({exe.permissions}, {exe.size} bytes)")
                else:
                    lines.append(f"  {exe.filename} ({exe.size} bytes)")

            # If there are more files, show a message
            if len(grouped[directory]) > 10:
                lines.append(f"  ... and {len(grouped[directory]) - 10} more files")

        return "\n".join(lines)

    @on(Button.Pressed, "#close-button")
    def on_close_button_pressed(self) -> None:
        """Handle close button press."""
        self.app.pop_screen()


class WishInput(Screen):
    """Screen for inputting a wish."""

    def compose(self) -> ComposeResult:
        """Compose the wish input screen."""
        yield Header(show_clock=True)
        yield Container(
            Label("wish✨️", id="wish-prompt", markup=False),
            Input(placeholder="Enter your wish here...", id="wish-input"),
            Container(
                Button("System Info", id="system-info-button", variant="default"),
                Button("Executables", id="executables-button", variant="default"),
                id="info-buttons-container",
            ),
            id="wish-container",
        )
        yield Footer()

    @on(Button.Pressed, "#system-info-button")
    def on_system_info_button_pressed(self) -> None:
        """Handle system info button press."""
        self.app.action_show_system_info()

    @on(Button.Pressed, "#executables-button")
    def on_executables_button_pressed(self) -> None:
        """Handle executables button press."""
        self.app.action_show_executables()

    @on(Input.Submitted)
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        wish_text = event.value.strip()
        if wish_text:
            # Create a new wish
            wish = Wish.create(wish_text)
            wish.state = WishState.DOING

            try:
                # Generate commands using WishManager (now async)
                commands, error = await self.app.wish_manager.generate_commands(wish_text)

                # Switch to command suggestion screen
                self.app.push_screen(CommandSuggestion(wish, commands, error))

            except CommandGenerationError as e:
                # Show error modal for command-generation errors
                self.app.push_screen(ErrorModal(str(e), e.api_response))


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
        # Start command execution and monitoring asynchronously
        asyncio.create_task(self.start_execution())

    async def start_execution(self) -> None:
        """Start command execution and monitoring."""
        # Execute commands
        await self.executor.execute_commands(self.wish, self.commands)

        # Monitor command status
        await self.monitor_commands()

    async def monitor_commands(self) -> None:
        """Asynchronously monitor command execution status."""
        while not self.all_completed:
            # Check status of running commands
            await self.tracker.check_status(self.wish)

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

    def __init__(self, backend_config=None, settings=None):
        """Initialize the Wish TUI application.

        Args:
            backend_config: Backend configuration (optional).
            settings: Application settings (optional).
        """
        super().__init__()
        self.settings = settings or Settings()
        self.wish_manager = WishManager(self.settings, backend_config)

        # Basic system information
        self.system_info = None
        self.system_info_state = "not_started"  # System information collection state

        # Executable files information
        self.executables = None
        self.executables_state = "not_started"  # Executable files collection state

    def update_info_buttons(self):
        """Update both info buttons based on collection state."""
        try:
            wish_input = self.query_one(WishInput)

            # Update System Info button
            system_info_button = wish_input.query_one("#system-info-button")
            if self.system_info_state == "collecting":
                system_info_button.label = "Collecting..."
                system_info_button.disabled = True
                system_info_button.variant = "warning"
            elif self.system_info_state == "ready":
                system_info_button.label = "System Info"
                system_info_button.disabled = False
                system_info_button.variant = "success"
            elif self.system_info_state == "error":
                system_info_button.label = "System Info (Error)"
                system_info_button.disabled = False
                system_info_button.variant = "error"
            else:  # not_started
                system_info_button.label = "System Info"
                system_info_button.disabled = False
                system_info_button.variant = "default"

            # Update Executables button
            executables_button = wish_input.query_one("#executables-button")
            if self.executables_state == "collecting":
                executables_button.label = "Collecting..."
                executables_button.disabled = True
                executables_button.variant = "warning"
            elif self.executables_state == "ready":
                executables_button.label = "Executables"
                executables_button.disabled = False
                executables_button.variant = "success"
            elif self.executables_state == "error":
                executables_button.label = "Executables (Error)"
                executables_button.disabled = False
                executables_button.variant = "error"
            else:  # not_started
                executables_button.label = "Executables"
                executables_button.disabled = False
                executables_button.variant = "default"
        except Exception:
            # Screen may not be displayed yet
            pass

    def update_system_info_button(self):
        """Update the System Info button based on collection state (legacy method)."""
        self.update_info_buttons()

    async def collect_system_info(self):
        """Collect system information."""
        # Set collection state to collecting
        self.system_info_state = "collecting"
        self.update_info_buttons()

        self.console.print("[bold green]Collecting system information...[/bold green]")

        try:
            # Get basic system information from backend
            self.system_info = await self.wish_manager.executor.backend.get_system_info()

            # Set collection state to ready
            self.system_info_state = "ready"
            self.update_info_buttons()

            # Display basic system information
            display_system_info(self.system_info, self.console)

        except Exception as e:
            # Set collection state to error
            self.system_info_state = "error"
            self.update_info_buttons()

            self.console.print(f"[bold red]Error collecting system information: {str(e)}[/bold red]")

            # Set minimal information even in case of error
            self.system_info = SystemInfo(
                os="Unknown (Error)", arch="Unknown", hostname="Unknown", username="Unknown", version=f"Error: {str(e)}"
            )

    def action_show_system_info(self) -> None:
        """Show system information in a modal window."""
        if self.system_info_state == "collecting":
            self.console.print("[yellow]System information is being collected. Please wait...[/yellow]")
            return

        if not self.system_info:
            self.console.print("[yellow]System information not available yet. Please wait...[/yellow]")
            return

        # Show system information in a modal window
        self.push_screen(SystemInfoModal(self.system_info))

    async def collect_executables(self):
        """Collect executable files information."""
        # Set collection state to collecting
        self.executables_state = "collecting"
        self.update_info_buttons()

        self.console.print("[bold green]Collecting executables information...[/bold green]")

        try:
            # Get executables from backend
            self.executables = await self.wish_manager.executor.backend.get_executables(
                collect_system_executables=False  # Only collect PATH executables by default
            )

            # Set collection state to ready
            self.executables_state = "ready"
            self.update_info_buttons()

            # Display executables information
            count = len(self.executables.executables)
            self.console.print(f"[green]✓ Collected {count} executables[/green]")

            # Show summary of executables by directory
            grouped = self.executables.group_by_directory()
            for directory, exes in sorted(grouped.items())[:5]:  # Show top 5 directories
                self.console.print(f"[green]{directory}: {len(exes)} files[/green]")

            if len(grouped) > 5:
                self.console.print(f"[green]... and {len(grouped) - 5} more directories[/green]")

        except Exception as e:
            # Set collection state to error
            self.executables_state = "error"
            self.update_info_buttons()

            self.console.print(f"[bold red]Error collecting executables: {str(e)}[/bold red]")

            # Set empty collection even in case of error
            from wish_models.system_info import ExecutableCollection

            self.executables = ExecutableCollection()

    def action_show_executables(self) -> None:
        """Show executables information in a modal window."""
        if self.executables_state == "not_started":
            # Start collection on first execution
            self.console.print("[yellow]Starting executables collection...[/yellow]")
            asyncio.create_task(self.collect_executables())
            return

        if self.executables_state == "collecting":
            self.console.print("[yellow]Executables information is being collected. Please wait...[/yellow]")
            return

        if not self.executables or not self.executables.executables:
            self.console.print("[yellow]No executables available.[/yellow]")
            return

        # Show executables information in a modal window
        self.push_screen(ExecutablesModal(self.executables))

    def on_mount(self) -> None:
        """Handle app mount event."""
        # Show the wish input screen first
        self.push_screen("wish_input")

        # Update button states
        self.update_info_buttons()

        # Then start collecting system information
        asyncio.create_task(self.collect_system_info())

        # Don't automatically start collecting executables
        # Let the user click the button to start collection


def main(backend_config=None, settings=None) -> None:
    """Run the Wish TUI application.

    Args:
        backend_config: Backend configuration (optional).
        settings: Application settings (optional).
    """
    app = WishApp(backend_config, settings)
    app.run()


if __name__ == "__main__":
    main()
