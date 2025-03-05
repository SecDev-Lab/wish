"""Command executor for wish_sh."""

import json
import subprocess
from pathlib import Path
from typing import Dict, Tuple, Optional

from wish_models import Wish, CommandResult, CommandState, LogFiles


class CommandExecutor:
    """Executes commands for a wish."""

    def __init__(self, wish_manager):
        """Initialize the command executor.
        
        Args:
            wish_manager: The WishManager instance providing necessary functionality.
        """
        self.wish_manager = wish_manager
        self.running_commands: Dict[int, Tuple[subprocess.Popen, CommandResult, Wish]] = {}

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
        log_dir = self.wish_manager.create_command_log_dirs(wish.id)
        stdout_path = log_dir / f"{cmd_num}.stdout"
        stderr_path = log_dir / f"{cmd_num}.stderr"
        log_files = LogFiles(stdout=stdout_path, stderr=stderr_path)

        # Create command result
        result = CommandResult.create(cmd_num, command, log_files)
        wish.command_results.append(result)

        with open(stdout_path, "w") as stdout_file, open(stderr_path, "w") as stderr_file:
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
                
            except PermissionError as e:
                error_msg = f"Permission error: No execution permission for command '{command}'"
                stderr_file.write(error_msg)
                self._handle_command_failure(result, wish, 126, CommandState.OTHERS, error_msg)
                
            except FileNotFoundError as e:
                error_msg = f"Command not found: '{command}'"
                stderr_file.write(error_msg)
                self._handle_command_failure(result, wish, 127, CommandState.OTHERS, error_msg)
                
            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                stderr_file.write(error_msg)
                self._handle_command_failure(result, wish, 1, CommandState.OTHERS, error_msg)

    def _handle_command_failure(self, result: CommandResult, wish: Wish, exit_code: int, state: CommandState, log_summary: str):
        """Common command failure handling."""
        result.finish(
            exit_code=exit_code,
            state=state,
            log_summarizer=lambda _: log_summary
        )
        wish.update_command_result(result)

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
                    log_summarizer=self.wish_manager.summarize_log
                )

                # Update the command result in the wish object
                wish.update_command_result(result)

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
        import time
        
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
                log_summarizer=self.wish_manager.summarize_log
            )

            # Update the command result in the wish object
            wish.update_command_result(result)

            del self.running_commands[cmd_num]

            return f"Command {cmd_num} cancelled."
        else:
            return f"Command {cmd_num} is not running."
