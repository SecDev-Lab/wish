"""Command executor for wish-command-execution."""

from pathlib import Path
from typing import Optional

from wish_models import LogFiles, Wish

from wish_command_execution.backend.base import Backend
from wish_command_execution.backend.bash import BashBackend


class CommandExecutor:
    """Executes commands for a wish."""

    def __init__(self, backend: Optional[Backend] = None, log_dir_creator=None):
        """Initialize the command executor.

        Args:
            backend: The backend to use for command execution.
            log_dir_creator: Function to create log directories.
        """
        self.backend = backend or BashBackend()
        self.log_dir_creator = log_dir_creator or self._default_log_dir_creator

    def _default_log_dir_creator(self, wish_id: str) -> Path:
        """Default implementation for creating log directories."""
        log_dir = Path(f"./logs/{wish_id}/commands")
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir

    def execute_commands(self, wish: Wish, commands: list[str]) -> None:
        """Execute a list of commands for a wish.

        Args:
            wish: The wish to execute commands for.
            commands: The list of commands to execute.
        """
        for i, cmd in enumerate(commands, 1):
            self.execute_command(wish, cmd, i)

    def execute_command(self, wish: Wish, command: str, cmd_num: int) -> None:
        """Execute a single command for a wish.

        Args:
            wish: The wish to execute the command for.
            command: The command to execute.
            cmd_num: The command number.
        """
        # Create log directories and files
        log_dir = self.log_dir_creator(wish.id)
        stdout_path = log_dir / f"{cmd_num}.stdout"
        stderr_path = log_dir / f"{cmd_num}.stderr"
        log_files = LogFiles(stdout=stdout_path, stderr=stderr_path)

        # Execute the command using the backend
        self.backend.execute_command(wish, command, cmd_num, log_files)

    def check_running_commands(self):
        """Check status of running commands and update their status."""
        self.backend.check_running_commands()

    def cancel_command(self, wish: Wish, cmd_num: int) -> str:
        """Cancel a running command.

        Args:
            wish: The wish to cancel the command for.
            cmd_num: The command number to cancel.

        Returns:
            A message indicating the result of the cancellation.
        """
        return self.backend.cancel_command(wish, cmd_num)
