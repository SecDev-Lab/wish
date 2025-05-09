"""Command executor for wish-command-execution."""

import logging
from pathlib import Path
from typing import List, Optional

from wish_models import CommandState, LogFiles, Wish
from wish_models.command_result import CommandInput

from wish_command_execution.backend.base import Backend
from wish_command_execution.backend.bash import BashBackend

# ロギング設定
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class CommandExecutor:
    """Executes commands for a wish."""

    def __init__(self, backend: Optional[Backend] = None, log_dir_creator=None, run_id=None):
        """Initialize the command executor.

        Args:
            backend: The backend to use for command execution.
            log_dir_creator: Function to create log directories.
            run_id: Run ID for step tracing.
        """
        self.run_id = run_id
        self.backend = backend or BashBackend(run_id=run_id)
        self.log_dir_creator = log_dir_creator or self._default_log_dir_creator

    def _default_log_dir_creator(self, wish_id: str) -> Path:
        """Default implementation for creating log directories."""
        log_dir = Path(f"./logs/{wish_id}/commands")
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir

    async def execute_commands(self, wish: Wish, command_inputs: List[CommandInput]) -> None:
        """Execute a list of commands for a wish.

        Args:
            wish: The wish to execute commands for.
            command_inputs: The list of command inputs to execute.
        """
        for i, cmd_input in enumerate(command_inputs, 1):
            command = cmd_input.command
            # タイムアウト値を取得
            timeout_sec = cmd_input.timeout_sec
            await self.execute_command(wish, command, i, timeout_sec)

    async def execute_command(self, wish: Wish, command: str, cmd_num: int, timeout_sec: int) -> None:
        """Execute a single command for a wish.

        Args:
            wish: The wish to execute the command for.
            command: The command to execute.
            cmd_num: The command number.
            timeout_sec: The timeout in seconds for this command.
        """
        # Create log directories and files
        log_dir = self.log_dir_creator(wish.id)
        stdout_path = log_dir / f"{cmd_num}.stdout"
        stderr_path = log_dir / f"{cmd_num}.stderr"
        log_files = LogFiles(stdout=stdout_path, stderr=stderr_path)

        # Execute the command using the backend
        await self.backend.execute_command(wish, command, cmd_num, log_files, timeout_sec)

    async def check_running_commands(self):
        """Check status of running commands and update their status."""
        await self.backend.check_running_commands()

    async def cancel_command(self, wish: Wish, cmd_num: int) -> str:
        """Cancel a running command.

        Args:
            wish: The wish to cancel the command for.
            cmd_num: The command number to cancel.

        Returns:
            A message indicating the result of the cancellation.
        """
        return await self.backend.cancel_command(wish, cmd_num)

    async def finish_command(self, wish: Wish, cmd_num: int, exit_code: int, state: CommandState = None):
        """Finish a command and send trace.

        Args:
            wish: The wish to finish the command for.
            cmd_num: The command number.
            exit_code: The exit code of the command.
            state: The state of the command.
        """
        # Find the command result
        result = None
        for cmd_result in wish.command_results:
            if cmd_result.num == cmd_num:
                result = cmd_result
                break

        if result:
            # Use BashBackend's finish_with_trace method if available
            if hasattr(self.backend, 'finish_with_trace'):
                await self.backend.finish_with_trace(
                    wish=wish,
                    result=result,
                    exit_code=exit_code,
                    state=state,
                    trace_name="Command Execution Complete"
                )
            else:
                # Fallback to just finishing the command
                result.finish(exit_code=exit_code, state=state)
