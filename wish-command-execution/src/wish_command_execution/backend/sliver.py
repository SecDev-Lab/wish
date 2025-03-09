"""Sliver C2 backend for command execution."""

import asyncio
import concurrent.futures
from typing import Any, Dict, Tuple

from sliver import SliverClient, SliverClientConfig
from wish_models import CommandResult, CommandState, Wish
from wish_models.executable_collection import ExecutableCollection
from wish_models.system_info import SystemInfo

from wish_command_execution.backend.base import Backend
from wish_command_execution.system_info import SystemInfoCollector


class SliverBackend(Backend):
    """Backend for executing commands using Sliver C2."""

    def __init__(self, session_id: str, client_config_path: str):
        """Initialize the Sliver backend.

        Args:
            session_id: The ID of the Sliver session to interact with.
            client_config_path: Path to the Sliver client configuration file.
        """
        self.session_id = session_id
        self.client_config_path = client_config_path
        self.client = None  # SliverClient instance
        self.interactive_session = None  # Interactive session
        # Track running commands (thread, result, wish)
        self.running_commands: Dict[int, Tuple[Any, CommandResult, Wish]] = {}

    async def _connect(self):
        """Connect to the Sliver server.

        Establishes a connection to the Sliver server and opens an interactive session
        with the specified session ID.
        """
        # Do nothing if already connected
        if self.client and self.interactive_session:
            return

        # Load client configuration from file
        config = SliverClientConfig.parse_config_file(self.client_config_path)
        self.client = SliverClient(config)

        # Connect to server
        await self.client.connect()

        # Connect to the specified session
        self.interactive_session = await self.client.interact_session(self.session_id)

    def execute_command(self, wish: Wish, command: str, cmd_num: int, log_files) -> None:
        """Execute a command through Sliver C2.

        Args:
            wish: The wish to execute the command for.
            command: The command to execute.
            cmd_num: The command number.
            log_files: The log files to write output to.
        """
        # Create command result
        result = CommandResult.create(cmd_num, command, log_files)
        wish.command_results.append(result)

        try:
            # Get the main event loop
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                # If no event loop exists in this thread, create a new one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # Run the async command in the main event loop
            future = asyncio.run_coroutine_threadsafe(
                self._execute_command_wrapper(
                    command, log_files.stdout, log_files.stderr, result, wish, cmd_num
                ),
                loop
            )

            # Add a callback to handle completion
            future.add_done_callback(
                lambda f: self._handle_command_completion(f, result, wish)
            )

            # Track the future for status updates
            self.running_commands[cmd_num] = (future, result, wish)

            # Return immediately for UI (non-blocking)
            return

        except Exception as e:
            # Handle errors in the main thread
            with open(log_files.stderr, "w") as stderr_file:
                error_msg = f"Sliver execution error: {str(e)}"
                stderr_file.write(error_msg)
            self._handle_command_failure(result, wish, 1, CommandState.OTHERS)

    async def _execute_command_wrapper(self, command, stdout_path, stderr_path, result, wish, cmd_num):
        """Wrapper to execute a command and handle its lifecycle.

        Args:
            command: The command to execute.
            stdout_path: Path to the file to write stdout to.
            stderr_path: Path to the file to write stderr to.
            result: The CommandResult object.
            wish: The Wish object.
            cmd_num: The command number.
        """
        try:
            # Connect to Sliver server
            await self._connect()

            # Execute the command
            cmd_result = await self.interactive_session.execute(command, [])

            # Write results to log files
            with open(stdout_path, "w") as stdout_file, open(stderr_path, "w") as stderr_file:
                if cmd_result.Stdout:
                    stdout_content = cmd_result.Stdout.decode('utf-8', errors='replace')
                    stdout_file.write(stdout_content)

                if cmd_result.Stderr:
                    stderr_content = cmd_result.Stderr.decode('utf-8', errors='replace')
                    stderr_file.write(stderr_content)

            # Update command result
            exit_code = cmd_result.Status if cmd_result.Status is not None else 0
            result.finish(exit_code=exit_code)

            # Update the command result in the wish object
            for i, cmd_result in enumerate(wish.command_results):
                if cmd_result.num == result.num:
                    wish.command_results[i] = result
                    break

        except Exception as e:
            # Handle errors
            with open(stderr_path, "w") as stderr_file:
                error_msg = f"Sliver execution error: {str(e)}"
                stderr_file.write(error_msg)
            self._handle_command_failure(result, wish, 1, CommandState.OTHERS)

    def _handle_command_failure(
        self, result: CommandResult, wish: Wish, exit_code: int, state: CommandState
    ):
        """Handle command failure.

        Args:
            result: The command result to update.
            wish: The wish associated with the command.
            exit_code: The exit code to set.
            state: The command state to set.
        """
        result.finish(
            exit_code=exit_code,
            state=state
        )
        # Update the command result in the wish object
        for i, cmd_result in enumerate(wish.command_results):
            if cmd_result.num == result.num:
                wish.command_results[i] = result
                break

    def _handle_command_completion(self, future: concurrent.futures.Future, result: CommandResult, wish: Wish) -> None:
        """Handle command completion from a Future.

        Args:
            future: The completed Future object.
            result: The CommandResult object.
            wish: The Wish object.
        """
        try:
            # Get the result (will raise exception if the coroutine raised an exception)
            future.result()

            # If we get here, the future completed successfully
            # The result should already be updated by _execute_command_wrapper
            # But check if it's still in DOING state (which would be unexpected)
            if result.state == CommandState.DOING:
                result.finish(
                    exit_code=0,  # Assume success if not otherwise set
                    state=CommandState.SUCCESS
                )

                # Update the command result in the wish object
                for i, cmd_result in enumerate(wish.command_results):
                    if cmd_result.num == result.num:
                        wish.command_results[i] = result
                        break
        except Exception:
            # Handle any exceptions that occurred in the coroutine
            # This should be rare since _execute_command_wrapper should catch most exceptions
            if result.state == CommandState.DOING:
                # Only update if still in DOING state
                result.finish(
                    exit_code=1,
                    state=CommandState.OTHERS
                )

                # Update the command result in the wish object
                for i, cmd_result in enumerate(wish.command_results):
                    if cmd_result.num == result.num:
                        wish.command_results[i] = result
                        break

    def check_running_commands(self):
        """Check status of running commands and update their status."""
        # Check each running command future
        for cmd_num, (future, _result, _wish) in list(self.running_commands.items()):
            # Check if future is done
            if future.done():
                # Future has completed, but the callback might not have run yet
                # The callback should handle updating the result

                # Remove from tracking
                del self.running_commands[cmd_num]

    def cancel_command(self, wish: Wish, cmd_num: int) -> str:
        """Cancel a running command.

        Args:
            wish: The wish to cancel the command for.
            cmd_num: The command number to cancel.

        Returns:
            A message indicating the result of the cancellation.
        """
        # Find the command result
        result = None
        for cmd_result in wish.command_results:
            if cmd_result.num == cmd_num:
                result = cmd_result
                break

        if result and result.state == CommandState.DOING:
            # If the command is in the running_commands dict, cancel the future
            if cmd_num in self.running_commands:
                future, _, _ = self.running_commands[cmd_num]
                # Cancel the future if possible
                future.cancel()
                # Remove from tracking
                del self.running_commands[cmd_num]

            # Mark the command as cancelled
            result.finish(
                exit_code=-1,  # Use -1 for cancelled commands
                state=CommandState.USER_CANCELLED
            )

            # Update the command result in the wish object
            for i, cmd_result in enumerate(wish.command_results):
                if cmd_result.num == result.num:
                    wish.command_results[i] = result
                    break

            return f"Command {cmd_num} cancelled."
        else:
            return f"Command {cmd_num} is not running."

    async def get_executables(self, collect_system_executables: bool = False) -> ExecutableCollection:
        """Get executable files information from the Sliver session.

        Args:
            collect_system_executables: Whether to collect executables from the entire system

        Returns:
            ExecutableCollection: Collection of executables
        """
        try:
            await self._connect()  # Ensure connection is established

            if not self.interactive_session:
                raise RuntimeError("No active Sliver session")

            executables = await SystemInfoCollector.collect_executables_from_session(
                self.interactive_session,
                collect_system_executables=collect_system_executables
            )
            return executables
        except Exception:
            # Return empty collection on error
            return ExecutableCollection()

    async def get_system_info(self) -> SystemInfo:
        """Get system information from the Sliver session.

        Args:
            collect_system_executables: Whether to collect executables from the entire system

        Returns:
            SystemInfo: Collected system information
        """
        try:
            await self._connect()  # Ensure connection is established

            if not self.interactive_session:
                raise RuntimeError("No active Sliver session")

            # Basic information collection
            info = SystemInfo(
                os=self.interactive_session.os,
                arch=self.interactive_session.arch,
                version=self.interactive_session.version,
                hostname=self.interactive_session.hostname,
                username=self.interactive_session.username,
                uid=self.interactive_session.uid,
                gid=self.interactive_session.gid,
                pid=self.interactive_session.pid
            )
            return info
        except Exception:
            raise
