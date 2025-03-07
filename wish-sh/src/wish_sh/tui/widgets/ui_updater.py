"""UI updater for command execution screen."""

from typing import Protocol

from wish_models import Wish


class WidgetQuerier(Protocol):
    """Protocol for querying widgets."""

    def query_one(self, selector: str) -> 'Widget':
        """Query a widget by selector."""
        ...


class Widget(Protocol):
    """Protocol for widgets."""

    def update(self, content: str) -> None:
        """Update the widget content."""
        ...


class UIUpdater:
    """Updates the UI for command execution."""

    def __init__(self, screen: WidgetQuerier):
        """Initialize the UI updater.

        Args:
            screen: The screen to update.
        """
        self.screen = screen

    def update_command_status(self, wish: Wish) -> None:
        """Update the UI with current command statuses.

        Args:
            wish: The wish to update the UI for.
        """
        for result in wish.command_results:
            if result:
                # Format the status text
                status = f"Status: {result.state.value}"
                if result.exit_code is not None:
                    status += f" (exit code: {result.exit_code})"

                # Add execution time if command is finished
                if result.finished_at and result.created_at:
                    execution_time = result.finished_at - result.created_at
                    status += f"\nExecution time: {execution_time}"

                if result.log_summary:
                    status += f"\nSummary: {result.log_summary}"

                # Update the status widget
                status_widget = self.screen.query_one(f"#command-status-{result.num}")
                status_widget.update(status)

    def show_completion_message(self, message: str) -> None:
        """Show a completion message.

        Args:
            message: The message to show.
        """
        execution_text = self.screen.query_one("#execution-text")
        execution_text.update(message)
