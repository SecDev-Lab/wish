"""Bash backend for command execution."""

import subprocess
import time
from typing import Dict, Tuple

from wish_models import CommandResult, CommandState, Wish

from wish_command_execution.backend.base import Backend


class BashBackend(Backend):
    """Backend for executing commands using bash."""

    def __init__(self, log_summarizer=None):
        """Initialize the bash backend.

        Args:
            log_summarizer: Function to summarize logs.
        """
        self.running_commands: Dict[int, Tuple[subprocess.Popen, CommandResult, Wish]] = {}
        self.log_summarizer = log_summarizer or (lambda _: "No log summary available")

    def execute_command(self, wish: Wish, command: str, cmd_num: int, log_files) -> None:
        """Execute a command using bash.

        Args:
            wish: The wish to execute the command for.
            command: The command to execute.
            cmd_num: The command number.
            log_files: The log files to write output to.
        """
        # Create command result
        result = CommandResult.create(cmd_num, command, log_files)
        wish.command_results.append(result)

        with open(log_files.stdout, "w") as stdout_file, open(log_files.stderr, "w") as stderr_file:
            try:
                # Start the process
                process = subprocess.Popen(command, stdout=stdout_file, stderr=stderr_file, shell=True, text=True)

                # Store in running commands dict
                self.running_commands[cmd_num] = (process, result, wish)

                # Wait for process completion (non-blocking return for UI)
                return

            except subprocess.SubprocessError as e:
                error_msg = f"Subprocess error: {str(e)}"
                stderr_file.write(error_msg)
                self._handle_command_failure(result, wish, 1, CommandState.OTHERS, error_msg)

            except PermissionError:
                error_msg = f"Permission error: No execution permission for command '{command}'"
                stderr_file.write(error_msg)
                self._handle_command_failure(result, wish, 126, CommandState.OTHERS, error_msg)

            except FileNotFoundError:
                error_msg = f"Command not found: '{command}'"
                stderr_file.write(error_msg)
                self._handle_command_failure(result, wish, 127, CommandState.OTHERS, error_msg)

            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                stderr_file.write(error_msg)
                self._handle_command_failure(result, wish, 1, CommandState.OTHERS, error_msg)

    def _handle_command_failure(
        self, result: CommandResult, wish: Wish, exit_code: int, state: CommandState, log_summary: str
    ):
        """Common command failure handling."""
        result.finish(
            exit_code=exit_code,
            state=state,
            log_summarizer=lambda _: log_summary
        )
        # Update the command result in the wish object
        # This is a workaround for Pydantic models that don't allow dynamic attribute assignment
        for i, cmd_result in enumerate(wish.command_results):
            if cmd_result.num == result.num:
                wish.command_results[i] = result
                break

    def check_running_commands(self):
        """Check status of running commands and update their status."""
        for idx, (process, result, wish) in list(self.running_commands.items()):
            if process.poll() is not None:  # Process has finished
                # Determine the state based on exit code
                state = CommandState.SUCCESS if process.returncode == 0 else CommandState.OTHERS

                # Mark the command as finished
                result.finish(
                    exit_code=process.returncode,
                    state=state,
                    log_summarizer=self.log_summarizer
                )

                # Update the command result in the wish object
                # This is a workaround for Pydantic models that don't allow dynamic attribute assignment
                for i, cmd_result in enumerate(wish.command_results):
                    if cmd_result.num == result.num:
                        wish.command_results[i] = result
                        break

                # Remove from running commands
                del self.running_commands[idx]

    def cancel_command(self, wish: Wish, cmd_num: int) -> str:
        """Cancel a running command.

        Args:
            wish: The wish to cancel the command for.
            cmd_num: The command number to cancel.

        Returns:
            A message indicating the result of the cancellation.
        """
        if cmd_num in self.running_commands:
            process, result, _ = self.running_commands[cmd_num]

            # Try to terminate the process
            try:
                process.terminate()
                time.sleep(0.5)
                if process.poll() is None:  # Process still running
                    process.kill()  # Force kill
            except Exception:
                pass  # Ignore errors in termination

            # Mark the command as cancelled
            result.finish(
                exit_code=-1,  # Use -1 for cancelled commands
                state=CommandState.USER_CANCELLED,
                log_summarizer=self.log_summarizer
            )

            # Update the command result in the wish object
            # This is a workaround for Pydantic models that don't allow dynamic attribute assignment
            for i, cmd_result in enumerate(wish.command_results):
                if cmd_result.num == result.num:
                    wish.command_results[i] = result
                    break

            del self.running_commands[cmd_num]

            return f"Command {cmd_num} cancelled."
        else:
            return f"Command {cmd_num} is not running."
