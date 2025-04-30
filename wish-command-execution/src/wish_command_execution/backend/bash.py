"""Bash backend for command execution."""

import logging
import os
import platform
import subprocess
import time
from typing import Dict, Tuple

from wish_models import CommandResult, CommandState, Wish
from wish_models.executable_collection import ExecutableCollection
from wish_models.system_info import SystemInfo
from wish_tools.tool_step_trace import main as step_trace

from wish_command_execution.backend.base import Backend
from wish_command_execution.system_info import SystemInfoCollector

# ロギング設定
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class BashBackend(Backend):
    """Backend for executing commands using bash."""

    def __init__(self, run_id=None):
        """Initialize the bash backend.

        Args:
            run_id: Run ID for step tracing.
        """
        self.running_commands: Dict[int, Tuple[subprocess.Popen, CommandResult, Wish]] = {}
        self.run_id = run_id

    def _add_command_start_trace(self, wish: Wish, command: str, timeout_sec: int):
        """Add step trace for command start.

        Args:
            wish: The wish object.
            command: The command to execute.
            timeout_sec: The timeout in seconds.
        """
        try:
            trace_message = f"# Command\n\n{command}\n\n# Timeout [sec]\n\n{timeout_sec}"
            step_trace(
                run_id=self.run_id if self.run_id else wish.id,
                trace_name="Command Execution Start",
                trace_message=trace_message
            )
        except Exception as e:
            print(f"Error adding step trace for command start: {str(e)}")

    def _add_step_trace(self, wish: Wish, result: CommandResult, trace_name: str, exec_time_sec: float = 0):
        """Add step trace for command execution.

        Args:
            wish: The wish object.
            result: The command result.
            trace_name: The name of the trace.
            exec_time_sec: The execution time in seconds.
        """
        try:
            # Read stdout and stderr if available
            stdout_content = ""
            stderr_content = ""
            try:
                if result.log_files and result.log_files.stdout and result.log_files.stdout.exists():
                    with open(result.log_files.stdout, "r") as f:
                        stdout_content = f.read()
                if result.log_files and result.log_files.stderr and result.log_files.stderr.exists():
                    with open(result.log_files.stderr, "r") as f:
                        stderr_content = f.read()
            except Exception as e:
                print(f"Error reading log files: {str(e)}")

            # Calculate execution time if not provided
            if exec_time_sec == 0 and result.created_at and result.finished_at:
                exec_time_sec = (result.finished_at - result.created_at).total_seconds()

            # Build trace message
            trace_message = (
                f"# Command\n\n{result.command}\n\n"
                f"# Timeout [sec]\n\n{result.timeout_sec}\n\n"
                f"# Exit Code\n\n{result.exit_code if result.exit_code is not None else 'N/A'}\n\n"
                f"# Execution Time [sec]\n\n{exec_time_sec:.2f}\n\n"
                f"# stdout\n\n{stdout_content}\n\n"
                f"# stderr\n\n{stderr_content}"
            )

            # Send step trace
            step_trace(
                run_id=self.run_id if self.run_id else wish.id,
                trace_name=trace_name,
                trace_message=trace_message
            )
        except Exception as e:
            print(f"Error adding step trace: {str(e)}")

    async def execute_command(self, wish: Wish, command: str, cmd_num: int, log_files, timeout_sec: int) -> None:
        """Execute a command using bash.

        Args:
            wish: The wish to execute the command for.
            command: The command to execute.
            cmd_num: The command number.
            log_files: The log files to write output to.
            timeout_sec: The timeout in seconds for this command.
        """
        # Create command result
        result = CommandResult.create(cmd_num, command, log_files)

        # Set timeout_sec in CommandResult
        result.timeout_sec = timeout_sec

        wish.command_results.append(result)

        # Add StepTrace for command execution start
        self._add_command_start_trace(wish, command, timeout_sec)

        with open(log_files.stdout, "w") as stdout_file, open(log_files.stderr, "w") as stderr_file:
            try:
                # Start the process (this is still synchronous, but the interface is async)
                process = subprocess.Popen(
                    command,
                    stdout=stdout_file,
                    stderr=stderr_file,
                    shell=True,
                    text=True
                )

                # Store in running commands dict with timeout information
                self.running_commands[cmd_num] = (process, result, wish)

                # Associate timeout information with the process
                process.timeout_sec = timeout_sec
                process.start_time = time.time()

                # Wait for process completion (non-blocking return for UI)
                return

            except subprocess.SubprocessError as e:
                error_msg = f"Subprocess error: {str(e)}"
                stderr_file.write(error_msg)
                self._handle_command_failure(result, wish, 1, CommandState.OTHERS)

            except PermissionError:
                error_msg = f"Permission error: No execution permission for command '{command}'"
                stderr_file.write(error_msg)
                self._handle_command_failure(result, wish, 126, CommandState.OTHERS)

            except FileNotFoundError:
                error_msg = f"Command not found: '{command}'"
                stderr_file.write(error_msg)
                self._handle_command_failure(result, wish, 127, CommandState.COMMAND_NOT_FOUND)

            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                stderr_file.write(error_msg)
                self._handle_command_failure(result, wish, 1, CommandState.OTHERS)

    def _handle_command_failure(
        self, result: CommandResult, wish: Wish, exit_code: int, state: CommandState
    ):
        """Common command failure handling."""
        result.finish(
            exit_code=exit_code,
            state=state
        )
        # Update the command result in the wish object
        # This is a workaround for Pydantic models that don't allow dynamic attribute assignment
        for i, cmd_result in enumerate(wish.command_results):
            if cmd_result.num == result.num:
                wish.command_results[i] = result
                break

        # Add StepTrace for command execution failure
        self._add_step_trace(wish, result, "Command Execution Complete", 0)

    async def check_running_commands(self):
        """Check status of running commands and update their status."""
        current_time = time.time()

        for idx, (process, result, wish) in list(self.running_commands.items()):
            # Check if process has finished
            if process.poll() is not None:  # Process has finished
                # Mark the command as finished with exit code
                result.finish(
                    exit_code=process.returncode,
                    state=CommandState.SUCCESS if process.returncode == 0 else CommandState.OTHERS
                )

                # Update the command result in the wish object
                for i, cmd_result in enumerate(wish.command_results):
                    if cmd_result.num == result.num:
                        wish.command_results[i] = result
                        break

                # Add StepTrace for command execution completion
                self._add_step_trace(wish, result, "Command Execution Complete")

                # Remove from running commands
                del self.running_commands[idx]

            # Check for timeout
            elif hasattr(process, 'timeout_sec') and hasattr(process, 'start_time'):
                elapsed_time = current_time - process.start_time
                if elapsed_time > process.timeout_sec:
                    # Timeout occurred
                    try:
                        process.terminate()
                        time.sleep(0.5)
                        if process.poll() is None:  # Still running
                            process.kill()  # Force kill
                    except Exception:
                        pass  # Ignore termination errors

                    # Record as timeout
                    with open(result.log_files.stderr, "a") as stderr_file:
                        stderr_file.write(f"\nCommand timed out after {process.timeout_sec} seconds\n")

                    result.finish(
                        exit_code=124,  # Exit code for timeout
                        state=CommandState.TIMEOUT
                    )

                    # Update the command result in the wish object
                    for i, cmd_result in enumerate(wish.command_results):
                        if cmd_result.num == result.num:
                            wish.command_results[i] = result
                            break

                    # Add StepTrace for command timeout
                    self._add_step_trace(wish, result, "Command Execution Complete", elapsed_time)

                    # Remove from running commands
                    del self.running_commands[idx]

    async def cancel_command(self, wish: Wish, cmd_num: int) -> str:
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
                state=CommandState.USER_CANCELLED
            )

            # Update the command result in the wish object
            # This is a workaround for Pydantic models that don't allow dynamic attribute assignment
            for i, cmd_result in enumerate(wish.command_results):
                if cmd_result.num == result.num:
                    wish.command_results[i] = result
                    break

            # Add StepTrace for command cancellation
            self._add_step_trace(wish, result, "Command Execution Complete")

            del self.running_commands[cmd_num]

            return f"Command {cmd_num} cancelled."
        else:
            return f"Command {cmd_num} is not running."

    async def get_executables(self, collect_system_executables: bool = False) -> ExecutableCollection:
        """Get executable files information from the local system.

        Args:
            collect_system_executables: Whether to collect executables from the entire system

        Returns:
            ExecutableCollection: Collection of executables
        """
        # Collect executables in PATH
        path_executables = SystemInfoCollector._collect_local_path_executables()

        # Optionally collect system-wide executables
        if collect_system_executables:
            system_executables = SystemInfoCollector._collect_local_system_executables()

            # Merge system executables into path executables
            for exe in system_executables.executables:
                path_executables.executables.append(exe)

        return path_executables

    async def get_system_info(self) -> SystemInfo:
        """Get system information from the local system.

        Args:
            collect_system_executables: Whether to collect executables from the entire system

        Returns:
            SystemInfo: Collected system information
        """
        # Basic information
        system = platform.system()
        info = SystemInfo(
            os=system,
            arch=platform.machine(),
            version=platform.version(),
            hostname=platform.node(),
            username=os.getlogin(),
            pid=os.getpid()
        )

        # Add UID and GID for Unix-like systems
        if system != "Windows":
            info.uid = str(os.getuid())
            info.gid = str(os.getgid())

        return info
