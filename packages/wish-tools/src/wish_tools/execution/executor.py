"""
Tool execution management
"""

import asyncio
import logging
import shlex
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .ansi_filter import AnsiFilter
from .msfconsole_executor import MsfconsoleExecutor

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result of tool execution"""

    command: str
    exit_code: int
    stdout: str
    stderr: str
    duration: float
    tool_name: str
    success: bool
    working_directory: str | None = None
    timeout_occurred: bool = False


class ToolExecutor:
    """Tool execution manager with async support"""

    def __init__(self):
        """Initialize executor"""
        self.active_processes: dict[str, asyncio.subprocess.Process] = {}
        self.msfconsole_executor = MsfconsoleExecutor()

    async def execute_command(
        self,
        command: str,
        tool_name: str,
        timeout: int = 300,
        working_directory: str | None = None,
        env_vars: dict[str, str] | None = None,
    ) -> ExecutionResult:
        """Execute a command with timeout"""
        # Validate command is not empty
        if not command or not command.strip():
            return ExecutionResult(
                command=command,
                exit_code=-5,
                stdout="",
                stderr="Empty command provided",
                duration=0.0,
                tool_name=tool_name,
                success=False,
                working_directory=working_directory,
                timeout_occurred=False,
            )

        # Handle legacy Metasploit command format
        if tool_name == "metasploit" and command.startswith("use "):
            # Convert legacy format to executable format
            logger.warning("Converting legacy Metasploit command format to msfconsole -x format")
            command = f"{command}; exit"
            tool_name = "msfconsole"

        # Handle msfconsole commands with specialized executor
        if tool_name == "msfconsole" or command.startswith("msfconsole"):
            return await self._execute_msfconsole_command(command, tool_name, timeout, working_directory, env_vars)

        # Prepare execution environment
        start_time = time.time()
        process_id = f"{tool_name}_{start_time}"

        # Set up environment variables
        env = None
        if env_vars:
            import os

            env = os.environ.copy()
            env.update(env_vars)

        # Validate working directory
        if working_directory:
            work_dir = Path(working_directory)
            if not work_dir.exists():
                raise ValueError(f"Working directory does not exist: {working_directory}")
            if not work_dir.is_dir():
                raise ValueError(f"Working directory is not a directory: {working_directory}")

        logger.info(f"Executing command: {command} (tool: {tool_name}, timeout: {timeout}s)")

        try:
            # Parse command first to handle quoted strings properly
            try:
                args = shlex.split(command)
                if not args:
                    raise ValueError("Command parsed to empty arguments")
            except ValueError as e:
                # If shlex fails, it might be due to unmatched quotes or other issues
                logger.error(f"Failed to parse command: {e}")
                return ExecutionResult(
                    command=command,
                    exit_code=-6,
                    stdout="",
                    stderr=f"Failed to parse command: {str(e)}",
                    duration=time.time() - start_time,
                    tool_name=tool_name,
                    success=False,
                    working_directory=working_directory,
                    timeout_occurred=False,
                )

            # Security check removed - commands are approved by humans
            # Shell metacharacters are allowed since all commands require explicit user approval

            # Create subprocess using exec (not shell) for security
            process = await asyncio.create_subprocess_exec(
                args[0],
                *args[1:],
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_directory,
                env=env,
            )

            # Track active process
            self.active_processes[process_id] = process

            try:
                # Wait for completion with timeout
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)

                duration = time.time() - start_time
                stdout_str = stdout.decode("utf-8", errors="replace") if stdout else ""
                stderr_str = stderr.decode("utf-8", errors="replace") if stderr else ""

                # Apply ANSI filtering for terminal output
                stdout_str = AnsiFilter.sanitize_terminal_output(stdout_str)
                stderr_str = AnsiFilter.sanitize_terminal_output(stderr_str)

                result = ExecutionResult(
                    command=command,
                    exit_code=process.returncode or 0,
                    stdout=stdout_str,
                    stderr=stderr_str,
                    duration=duration,
                    tool_name=tool_name,
                    success=(process.returncode == 0),
                    working_directory=working_directory,
                    timeout_occurred=False,
                )

                logger.info(f"Command completed: {command} (exit_code: {result.exit_code}, duration: {duration:.2f}s)")
                return result

            except TimeoutError:
                # Handle timeout
                logger.warning(f"Command timed out after {timeout}s: {command}")

                # Terminate process gracefully
                await self._terminate_process(process, timeout=10)

                duration = time.time() - start_time

                return ExecutionResult(
                    command=command,
                    exit_code=-1,
                    stdout="",
                    stderr=f"Command timed out after {timeout} seconds",
                    duration=duration,
                    tool_name=tool_name,
                    success=False,
                    working_directory=working_directory,
                    timeout_occurred=True,
                )

        except FileNotFoundError as e:
            # Tool not found
            duration = time.time() - start_time
            error_msg = f"Tool not found: {tool_name}. {str(e)}"
            logger.error(error_msg)

            return ExecutionResult(
                command=command,
                exit_code=-2,
                stdout="",
                stderr=error_msg,
                duration=duration,
                tool_name=tool_name,
                success=False,
                working_directory=working_directory,
            )

        except PermissionError as e:
            # Permission denied
            duration = time.time() - start_time
            error_msg = f"Permission denied: {str(e)}"
            logger.error(error_msg)

            return ExecutionResult(
                command=command,
                exit_code=-3,
                stdout="",
                stderr=error_msg,
                duration=duration,
                tool_name=tool_name,
                success=False,
                working_directory=working_directory,
            )

        except Exception as e:
            # Unexpected error
            duration = time.time() - start_time
            error_msg = f"Unexpected error executing command: {str(e)}"
            logger.error(error_msg, exc_info=True)

            return ExecutionResult(
                command=command,
                exit_code=-4,
                stdout="",
                stderr=error_msg,
                duration=duration,
                tool_name=tool_name,
                success=False,
                working_directory=working_directory,
            )

        finally:
            # Clean up process tracking
            self.active_processes.pop(process_id, None)

    async def _execute_msfconsole_command(
        self,
        command: str,
        tool_name: str,
        timeout: int,
        working_directory: str | None,
        env_vars: dict[str, str] | None,
    ) -> ExecutionResult:
        """Execute msfconsole command with specialized handler"""
        start_time = time.time()

        try:
            # Extract msfconsole command if it's in full form
            if command.startswith("msfconsole"):
                # Extract the -x argument content
                import re

                match = re.search(r'-x\s+["\']([^"\']*)["\']', command)
                if match:
                    command = match.group(1)
                else:
                    # Fallback to removing msfconsole prefix
                    command = command.replace("msfconsole -q -x ", "").strip("\"'")

            stdout, stderr, exit_code = await self.msfconsole_executor.execute_msfconsole_command(
                command=command,
                timeout=timeout,
                working_directory=working_directory,
                env_vars=env_vars,
            )

            duration = time.time() - start_time

            result = ExecutionResult(
                command=f"msfconsole -q -x '{command}; exit'",
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                duration=duration,
                tool_name=tool_name,
                success=(exit_code == 0),
                working_directory=working_directory,
                timeout_occurred=False,
            )

            logger.info(f"Msfconsole command completed: {command} (exit_code: {exit_code}, duration: {duration:.2f}s)")
            return result

        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Error executing msfconsole command: {str(e)}"
            logger.error(error_msg, exc_info=True)

            return ExecutionResult(
                command=f"msfconsole -q -x '{command}; exit'",
                exit_code=-1,
                stdout="",
                stderr=error_msg,
                duration=duration,
                tool_name=tool_name,
                success=False,
                working_directory=working_directory,
                timeout_occurred=False,
            )

    async def _terminate_process(self, process: asyncio.subprocess.Process, timeout: int = 10) -> None:
        """Gracefully terminate a process"""
        try:
            # First try SIGTERM
            process.terminate()

            # Wait for graceful shutdown
            try:
                await asyncio.wait_for(process.wait(), timeout=timeout)
                logger.debug("Process terminated gracefully")
                return
            except TimeoutError:
                logger.warning("Process did not terminate gracefully, using SIGKILL")

            # Force kill if necessary
            process.kill()
            await process.wait()
            logger.debug("Process killed forcefully")

        except ProcessLookupError:
            # Process already terminated
            logger.debug("Process already terminated")
        except Exception as e:
            logger.error(f"Error terminating process: {e}")

    async def execute_tool_with_args(
        self,
        tool_name: str,
        args: list[str],
        timeout: int = 300,
        working_directory: str | None = None,
        env_vars: dict[str, str] | None = None,
    ) -> ExecutionResult:
        """Execute a tool with properly quoted arguments"""
        # Build command with proper shell escaping
        escaped_args = [shlex.quote(arg) for arg in args]
        command = f"{tool_name} {' '.join(escaped_args)}"

        return await self.execute_command(
            command=command,
            tool_name=tool_name,
            timeout=timeout,
            working_directory=working_directory,
            env_vars=env_vars,
        )

    async def cancel_all_executions(self) -> None:
        """Cancel all active command executions"""
        logger.info(f"Cancelling {len(self.active_processes)} active processes")

        for process_id, process in list(self.active_processes.items()):
            logger.debug(f"Cancelling process: {process_id}")
            await self._terminate_process(process)

        self.active_processes.clear()

    def get_active_executions(self) -> dict[str, dict[str, Any]]:
        """Get information about currently active executions"""
        active = {}
        for process_id, process in self.active_processes.items():
            active[process_id] = {
                "pid": process.pid,
                "returncode": process.returncode,
            }
        return active
