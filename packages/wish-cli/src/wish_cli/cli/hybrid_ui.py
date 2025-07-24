"""Hybrid UI management for wish CLI."""

import logging
import os
from typing import Any

from wish_cli.ui.minimal_input_app import MinimalInputApp

# Removed unused import: TerminalOutput
from wish_cli.ui.ui_manager import WishUIManager

logger = logging.getLogger(__name__)


class HybridUIManager:
    """Hybrid UI management class for combining terminal output and input app."""

    def __init__(self, ui_manager: WishUIManager, state_manager: Any = None, job_manager: Any = None):
        self.ui_manager = ui_manager
        # Removed unused terminal_output
        self.input_app: MinimalInputApp | None = None
        self.state_manager = state_manager
        self.job_manager = job_manager

    def initialize_input_app(self, command_callback: Any) -> MinimalInputApp:
        """Initialize the minimal input app with command callback."""
        logger.debug("Initializing MinimalInputApp...")
        self.input_app = MinimalInputApp(state_manager=self.state_manager, job_manager=self.job_manager)
        self.input_app.set_command_callback(command_callback)
        logger.debug(f"MinimalInputApp created: {self.input_app}")

        # Immediately setup output callback - don't wait for on_mount
        self._setup_output_callback()

        # Display banner and setup callback when Textual app initializes
        original_on_mount = self.input_app.on_mount

        def enhanced_on_mount() -> None:
            logger.debug("Running enhanced_on_mount...")
            original_on_mount()
            self._display_banner()
            # Re-setup callback in case it was cleared
            self._setup_output_callback()

        # Type ignore for method assignment
        self.input_app.on_mount = enhanced_on_mount  # type: ignore[method-assign]
        logger.info("MinimalInputApp initialization complete")
        return self.input_app

    def _display_banner(self) -> None:
        """Display welcome banner."""
        if not self.input_app:
            return

        cwd = os.getcwd()
        self.input_app.write_output("[cyan]✻ Welcome to wish![/cyan]")
        self.input_app.write_output("")
        self.input_app.write_output("/help for help, /status for your current setup")
        self.input_app.write_output("Type your commands or questions naturally")
        self.input_app.write_output("")
        self.input_app.write_output(f"[dim]cwd: {cwd}[/dim]")
        self.input_app.write_output("")

    def _setup_output_callback(self) -> None:
        """Setup output callback for UI manager."""
        logger.debug("Setting up output callback...")
        if self.ui_manager and self.input_app:

            def callback(msg: str) -> None:
                if self.input_app:
                    self.input_app.write_output(msg)

            self.ui_manager.set_output_callback(callback)

            # Also set reference to MinimalInputApp
            if self.input_app is not None:
                self.ui_manager._input_app = self.input_app  # type: ignore[assignment]

            logger.info(f"Output callback setup complete - UI manager: {self.ui_manager}, input_app: {self.input_app}")
        else:
            logger.warning(f"Cannot setup output callback - UI manager: {self.ui_manager}, input_app: {self.input_app}")

    def write_output(self, message: str) -> None:
        """Write output to the input app."""
        if self.input_app:
            self.input_app.write_output(message)

    def write_command_echo(self, command: str) -> None:
        """Write command echo to the input app."""
        if self.input_app:
            self.input_app.write_output(f"[dim]> {command}[/dim]")

    def write_thinking_message(self) -> None:
        """Write thinking message for natural language processing."""
        if self.input_app:
            self.input_app.write_output("[dim]Generating execution plan...[/dim]")

    def write_error(self, error_message: str) -> None:
        """Write error message to the input app."""
        if self.input_app:
            self.input_app.write_output(f"[error]{error_message}[/error]")

    def write_warning(self, warning_message: str) -> None:
        """Write warning message to the input app."""
        if self.input_app:
            self.input_app.write_output(f"[warning]{warning_message}[/warning]")

    def write_info(self, info_message: str) -> None:
        """Write info message to the input app."""
        if self.input_app:
            self.input_app.write_output(f"[info]{info_message}[/info]")

    def get_command_history(self) -> list:
        """Get command history from input app."""
        if self.input_app:
            return self.input_app.get_command_history()
        return []

    def exit_app(self) -> None:
        """Exit the input app."""
        if self.input_app:
            self.input_app.exit()

    async def run_app(self) -> None:
        """Run the input app in inline mode."""
        if self.input_app:
            # Ensure compatibility in tmux environment
            import os

            if "TMUX" in os.environ:
                # Minimize Textual's control sequences
                os.environ["TEXTUAL_INLINE"] = "1"
                os.environ["TEXTUAL_COLOR_SYSTEM"] = "standard"

            await self.input_app.run_async(inline=True)
