"""Sliver C2 backend for command execution."""

import asyncio
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
            # Run the async command in a separate thread with its own event loop
            import threading

            def run_async_command():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    # Pass file paths instead of file handles
                    loop.run_until_complete(
                        self._execute_command_wrapper(
                            command, log_files.stdout, log_files.stderr, result, wish, cmd_num
                        )
                    )
                except Exception as e:
                    # Handle errors in the thread
                    with open(log_files.stderr, "w") as stderr_file:
                        error_msg = f"Sliver execution error in thread: {str(e)}"
                        stderr_file.write(error_msg)
                    self._handle_command_failure(result, wish, 1, CommandState.OTHERS)
                finally:
                    loop.close()

            # Start the thread
            thread = threading.Thread(target=run_async_command)
            thread.daemon = True  # Make thread daemon so it doesn't block program exit
            thread.start()

            # Track the thread for status updates
            self.running_commands[cmd_num] = (thread, result, wish)

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

    def check_running_commands(self):
        """Check status of running commands and update their status."""
        # Check each running command thread
        for cmd_num, (thread, result, wish) in list(self.running_commands.items()):
            # Check if thread is still alive
            if not thread.is_alive():
                # Thread has completed, but the result might not be updated
                # if there was an error in the thread
                if result.state == CommandState.DOING:
                    # If still in DOING state, update it to SUCCESS
                    # (if there was an error, it would have been updated already)
                    result.finish(
                        exit_code=0,  # Assume success if not otherwise set
                        state=CommandState.SUCCESS
                    )

                    # Update the command result in the wish object
                    for i, cmd_result in enumerate(wish.command_results):
                        if cmd_result.num == result.num:
                            wish.command_results[i] = result
                            break

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

    async def get_basic_system_info(self) -> SystemInfo:
        """Get basic system information from the Sliver session.

        Returns:
            SystemInfo: Collected basic system information
        """
        try:
            await self._connect()  # Ensure connection is established

            if not self.interactive_session:
                raise RuntimeError("No active Sliver session")

            info = await SystemInfoCollector.collect_basic_info_from_session(self.interactive_session)
            return info
        except Exception:
            raise

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

    async def get_system_info(self, collect_system_executables: bool = False) -> SystemInfo:
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

            # Use the new collect_from_session method
            info, _ = await SystemInfoCollector.collect_from_session(
                self.interactive_session,
                collect_system_executables=collect_system_executables
            )
            return info
        except Exception:
            raise
