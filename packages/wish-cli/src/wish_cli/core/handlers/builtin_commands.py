"""Built-in command handlers for wish CLI."""

import logging
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class OutputWriter(Protocol):
    """Protocol for output writing."""

    def write_output(self, message: str) -> None:
        """Write output message."""
        ...

    def get_command_history(self) -> list[str]:
        """Get command history."""
        ...


class BuiltinCommandHandler:
    """Handler for built-in CLI commands."""

    def __init__(self, output_writer: OutputWriter):
        self.output_writer = output_writer

    def show_help(self) -> None:
        """Show help information."""
        self.output_writer.write_output("[wish.step]●[/wish.step] Available commands:")
        self.output_writer.write_output(
            "  [wish.step]⎿[/wish.step] [wish.command]/help, ?[/wish.command] - Show this help"
        )
        self.output_writer.write_output(
            "  [wish.step]⎿[/wish.step] [wish.command]/status[/wish.command] - Show current status"
        )
        self.output_writer.write_output(
            "  [wish.step]⎿[/wish.step] [wish.command]/history[/wish.command] - Show command history"
        )
        self.output_writer.write_output(
            "  [wish.step]⎿[/wish.step] [wish.command]/jobs[/wish.command] - Show running jobs"
        )
        self.output_writer.write_output(
            "  [wish.step]⎿[/wish.step] [wish.command]/scope[/wish.command] - Manage target scope"
        )
        self.output_writer.write_output(
            "  [wish.step]⎿[/wish.step] [wish.command]exit, quit[/wish.command] - Exit the application"
        )
        self.output_writer.write_output("")
        self.output_writer.write_output("[wish.step]●[/wish.step] AI Commands:")
        self.output_writer.write_output("  [wish.step]⎿[/wish.step] Ask questions about penetration testing")
        self.output_writer.write_output("  [wish.step]⎿[/wish.step] Request commands to run")
        self.output_writer.write_output("  [wish.step]⎿[/wish.step] Get advice on next steps")

    def show_history(self) -> None:
        """Show command history."""
        command_history = self.output_writer.get_command_history()
        if not command_history:
            self.output_writer.write_output("[wish.step]●[/wish.step] [dim]No command history available[/dim]")
            return

        self.output_writer.write_output("[wish.step]●[/wish.step] Command History:")
        recent_history = command_history[-10:]  # Latest 10 commands

        for i, cmd in enumerate(recent_history, 1):
            if "\n" in cmd:
                first_line = cmd.split("\n")[0]
                line_count = len(cmd.split("\n"))
                self.output_writer.write_output(
                    f"  [wish.step]⎿[/wish.step] {i}. [wish.command]{first_line}[/wish.command] "
                    f"[dim](+{line_count - 1} more lines)[/dim]"
                )
            else:
                self.output_writer.write_output(f"  [wish.step]⎿[/wish.step] {i}. [wish.command]{cmd}[/wish.command]")
