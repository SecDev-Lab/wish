"""Base backend interface for command execution."""

from wish_models import Wish


class Backend:
    """Base class for command execution backends."""

    def execute_command(self, wish: Wish, command: str, cmd_num: int, log_files) -> None:
        """Execute a command for a wish.

        Args:
            wish: The wish to execute the command for.
            command: The command to execute.
            cmd_num: The command number.
            log_files: The log files to write output to.
        """
        raise NotImplementedError

    def check_running_commands(self):
        """Check status of running commands and update their status."""
        raise NotImplementedError

    def cancel_command(self, wish: Wish, cmd_num: int) -> str:
        """Cancel a running command.

        Args:
            wish: The wish to cancel the command for.
            cmd_num: The command number to cancel.

        Returns:
            A message indicating the result of the cancellation.
        """
        raise NotImplementedError
