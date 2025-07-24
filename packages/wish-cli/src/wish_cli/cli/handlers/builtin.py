"""Built-in command handlers for wish CLI."""

import logging
from typing import Any

from wish_cli.ui.ui_manager import WishUIManager

logger = logging.getLogger(__name__)


class BuiltinCommandHandler:
    """Built-in command handler for common CLI operations."""

    def __init__(self, input_app: Any | None = None, ui_manager: WishUIManager | None = None):
        self.input_app = input_app
        self.ui_manager = ui_manager

    def set_input_app(self, input_app: Any) -> None:
        """Set the input app for output operations."""
        self.input_app = input_app

    def handle_help(self) -> None:
        """Handle help command."""
        if not self.input_app:
            return

        self.input_app.write_output("[wish.step]●[/wish.step] Available commands:")
        self.input_app.write_output("  [wish.step]⎿[/wish.step] [wish.command]/help, ?[/wish.command] - Show this help")
        self.input_app.write_output(
            "  [wish.step]⎿[/wish.step] [wish.command]/status[/wish.command] - Show current status"
        )
        self.input_app.write_output(
            "  [wish.step]⎿[/wish.step] [wish.command]/history[/wish.command] - Show command history"
        )
        self.input_app.write_output("  [wish.step]⎿[/wish.step] [wish.command]/jobs[/wish.command] - Show running jobs")
        self.input_app.write_output(
            "  [wish.step]⎿[/wish.step] [wish.command]exit, quit[/wish.command] - Exit the application"
        )
        self.input_app.write_output("")
        self.input_app.write_output("[wish.step]●[/wish.step] AI Commands:")
        self.input_app.write_output("  [wish.step]⎿[/wish.step] Ask questions about penetration testing")
        self.input_app.write_output("  [wish.step]⎿[/wish.step] Request commands to run")
        self.input_app.write_output("  [wish.step]⎿[/wish.step] Get advice on next steps")

    def handle_history(self) -> None:
        """Handle history command."""
        if not self.input_app:
            return

        command_history = self.input_app.get_command_history()
        if not command_history:
            self.input_app.write_output("[wish.step]●[/wish.step] [dim]No command history available[/dim]")
            return

        self.input_app.write_output("[wish.step]●[/wish.step] Command History:")
        recent_history = command_history[-10:]  # Latest 10 items

        for i, cmd in enumerate(recent_history, 1):
            if "\n" in cmd:
                first_line = cmd.split("\n")[0]
                line_count = len(cmd.split("\n"))
                self.input_app.write_output(
                    f"  [wish.step]⎿[/wish.step] {i}. [wish.command]{first_line}[/wish.command] "
                    f"[dim](+{line_count - 1} more lines)[/dim]"
                )
            else:
                self.input_app.write_output(f"  [wish.step]⎿[/wish.step] {i}. [wish.command]{cmd}[/wish.command]")

    def handle_jobs(self) -> None:
        """Handle jobs command."""
        if not self.input_app or not self.ui_manager:
            return

        running_jobs = self.ui_manager.get_running_jobs()
        if not running_jobs:
            self.input_app.write_output("[wish.step]●[/wish.step] [dim]No running jobs[/dim]")
            return

        self.input_app.write_output("[wish.step]●[/wish.step] Running Jobs:")
        for job_id in running_jobs:
            details = self.ui_manager.get_job_details(job_id)
            if details:
                tool_name = details.get("tool_name", "unknown")
                status = details.get("status", "unknown")
                started_at = details.get("started_at", "unknown")
                self.input_app.write_output(
                    f"  [wish.step]⎿[/wish.step] {job_id}: {tool_name} ({status}) - started {started_at}"
                )

    def handle_exit(self) -> None:
        """Handle exit command."""
        if self.input_app:
            self.input_app.write_output("[info]Goodbye![/info]")
            self.input_app.exit()
