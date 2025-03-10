"""Sliver C2 backend for command execution."""

import logging
import sys

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

    async def _connect(self):
        """Connect to the Sliver server.

        Establishes a connection to the Sliver server and opens an interactive session
        with the specified session ID.
        """
        logger = logging.getLogger(__name__)
        # Do nothing if already connected
        if self.client and self.interactive_session:
            logger.debug("Already connected to Sliver server")
            return

        logger.debug(f"Loading client configuration from {self.client_config_path}")
        # Load client configuration from file
        config = SliverClientConfig.parse_config_file(self.client_config_path)
        self.client = SliverClient(config)

        # Connect to server
        logger.debug("Connecting to Sliver server")
        await self.client.connect()
        logger.debug("Connected to Sliver server")

        # Connect to the specified session
        logger.debug(f"Connecting to session {self.session_id}")
        self.interactive_session = await self.client.interact_session(self.session_id)
        logger.debug(f"Connected to session: {self.interactive_session}")

        # Check if the session is dead
        if self.interactive_session.is_dead:
            error_msg = "Error: Sliver session is in an invalid state. Cannot connect."
            logger.error(error_msg)
            print(error_msg, file=sys.stderr)
            sys.exit(1)

    async def execute_command(self, wish: Wish, command: str, cmd_num: int, log_files) -> None:
        """Execute a command through Sliver C2.

        Args:
            wish: The wish to execute the command for.
            command: The command to execute.
            cmd_num: The command number.
            log_files: The log files to write output to.
        """
        logger = logging.getLogger(__name__)
        logger.debug(f"SliverBackend.execute_command: Starting execution of command: {command}")
        
        # Create command result
        result = CommandResult.create(cmd_num, command, log_files)
        wish.command_results.append(result)
        logger.debug(f"Created CommandResult for command {cmd_num}")

        try:
            # Connect to Sliver server first
            logger.debug("Connecting to Sliver server")
            await self._connect()
            logger.debug(f"Connected to Sliver server, interactive_session: {self.interactive_session}")

            # Execute the command directly
            try:
                # Execute the command
                # Windowsシステムの場合、コマンドをcmd.exe経由で実行する
                os_type = self.interactive_session.os.lower()
                if "windows" in os_type:
                    # Windowsの場合、cmd.exeを使用して引数を正しく分割
                    logger.debug(f"Target OS is Windows, using cmd.exe with arguments")
                    # コマンドを分割
                    cmd_args = ['/C'] + command.split()
                    logger.debug(f"Command: cmd.exe, Args: {cmd_args}")
                    cmd_result = await self.interactive_session.execute('cmd.exe', cmd_args)
                else:
                    # Linux/macOSの場合は分割して実行
                    logger.debug(f"Executing command via interactive_session: {command}")
                    # 単純な分割（より複雑なケースでは改善が必要かもしれません）
                    cmd_parts = command.split()
                    cmd_name = cmd_parts[0]
                    cmd_args = cmd_parts[1:] if len(cmd_parts) > 1 else []
                    logger.debug(f"Command: {cmd_name}, Args: {cmd_args}")
                    cmd_result = await self.interactive_session.execute(cmd_name, cmd_args)
                logger.debug(f"Command executed, result: status={cmd_result.Status}")
                
                # Write results to log files
                logger.debug(f"Writing results to log files: {log_files}")
                with open(log_files.stdout, "w") as stdout_file, open(log_files.stderr, "w") as stderr_file:
                    if cmd_result.Stdout:
                        stdout_content = cmd_result.Stdout.decode('utf-8', errors='replace')
                        stdout_file.write(stdout_content)
                        logger.debug(f"Wrote {len(stdout_content)} bytes to stdout file")

                    if cmd_result.Stderr:
                        stderr_content = cmd_result.Stderr.decode('utf-8', errors='replace')
                        stderr_file.write(stderr_content)
                        logger.debug(f"Wrote {len(stderr_content)} bytes to stderr file")

                # Update command result
                exit_code = cmd_result.Status if cmd_result.Status is not None else 0
                logger.debug(f"Finishing command with exit_code: {exit_code}")
                result.finish(exit_code=exit_code)
                logger.debug(f"Command result updated: {result}")

                # Update the command result in the wish object
                for i, cmd_result in enumerate(wish.command_results):
                    if cmd_result.num == result.num:
                        wish.command_results[i] = result
                        logger.debug(f"Updated command result in wish object at index {i}")
                        break

            except Exception as e:
                # Handle errors
                logger.exception(f"Error executing command: {e}")
                with open(log_files.stderr, "w") as stderr_file:
                    error_msg = f"Sliver execution error: {str(e)}"
                    stderr_file.write(error_msg)
                self._handle_command_failure(result, wish, 1, CommandState.OTHERS)
                logger.debug("Command failure handled")

        except Exception as e:
            # Handle errors in the main thread
            logger.exception(f"Error in main thread: {e}")
            with open(log_files.stderr, "w") as stderr_file:
                error_msg = f"Sliver execution error: {str(e)}"
                stderr_file.write(error_msg)
            self._handle_command_failure(result, wish, 1, CommandState.OTHERS)
            logger.debug("Command failure handled (main thread)")

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
        logger = logging.getLogger(__name__)
        logger.debug(f"Handling command failure: exit_code={exit_code}, state={state}")
        
        result.finish(
            exit_code=exit_code,
            state=state
        )
        logger.debug(f"Command result updated with failure state: {result}")
        
        # Update the command result in the wish object
        for i, cmd_result in enumerate(wish.command_results):
            if cmd_result.num == result.num:
                wish.command_results[i] = result
                logger.debug(f"Updated failed command result in wish object at index {i}")
                break

    async def check_running_commands(self):
        """Check status of running commands and update their status."""
        # In the new async design, there are no futures to track
        # This method is kept for compatibility with the Backend interface
        pass

    async def cancel_command(self, wish: Wish, cmd_num: int) -> str:
        """Cancel a running command.

        Args:
            wish: The wish to cancel the command for.
            cmd_num: The command number to cancel.

        Returns:
            A message indicating the result of the cancellation.
        """
        logger = logging.getLogger(__name__)
        logger.debug(f"Cancelling command {cmd_num}")
        
        # Find the command result
        result = None
        for cmd_result in wish.command_results:
            if cmd_result.num == cmd_num:
                result = cmd_result
                break

        if result and result.state == CommandState.DOING:
            # In the new async design, we don't have futures to cancel
            # We can only mark the command as cancelled in the result
            logger.debug(f"Command {cmd_num} is running, marking as cancelled")

            # Mark the command as cancelled
            result.finish(
                exit_code=-1,  # Use -1 for cancelled commands
                state=CommandState.USER_CANCELLED
            )
            logger.debug(f"Command result updated with cancelled state: {result}")

            # Update the command result in the wish object
            for i, cmd_result in enumerate(wish.command_results):
                if cmd_result.num == result.num:
                    wish.command_results[i] = result
                    logger.debug(f"Updated cancelled command result in wish object at index {i}")
                    break

            return f"Command {cmd_num} cancelled."
        else:
            logger.debug(f"Command {cmd_num} is not running, cannot cancel")
            return f"Command {cmd_num} is not running."

    async def get_executables(self, collect_system_executables: bool = False) -> ExecutableCollection:
        """Get executable files information from the Sliver session.

        Args:
            collect_system_executables: Whether to collect executables from the entire system

        Returns:
            ExecutableCollection: Collection of executables
        """
        logger = logging.getLogger(__name__)
        logger.debug(f"Getting executables, collect_system_executables={collect_system_executables}")
        
        try:
            await self._connect()  # Ensure connection is established
            logger.debug("Connection established")

            if not self.interactive_session:
                logger.error("No active Sliver session")
                raise RuntimeError("No active Sliver session")

            logger.debug("Collecting executables from session")
            executables = await SystemInfoCollector.collect_executables_from_session(
                self.interactive_session,
                collect_system_executables=collect_system_executables
            )
            logger.debug(f"Collected {len(executables.executables)} executables")
            return executables
        except Exception as e:
            logger.exception(f"Error collecting executables: {e}")
            # Return empty collection on error
            return ExecutableCollection()

    async def get_system_info(self) -> SystemInfo:
        """Get system information from the Sliver session.

        Args:
            collect_system_executables: Whether to collect executables from the entire system

        Returns:
            SystemInfo: Collected system information
        """
        logger = logging.getLogger(__name__)
        logger.debug("Getting system information")
        
        try:
            await self._connect()  # Ensure connection is established
            logger.debug("Connection established")

            if not self.interactive_session:
                logger.error("No active Sliver session")
                raise RuntimeError("No active Sliver session")

            # Basic information collection
            logger.debug("Collecting basic system information")
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
            logger.debug(f"System information collected: {info}")
            return info
        except Exception as e:
            logger.exception(f"Error collecting system information: {e}")
            raise
