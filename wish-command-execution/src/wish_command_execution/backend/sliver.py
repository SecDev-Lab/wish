"""Sliver C2 backend for command execution."""

import logging
import sys

from sliver import SliverClient, SliverClientConfig
from wish_models import CommandResult, CommandState, Wish
from wish_models.executable_collection import ExecutableCollection
from wish_models.system_info import SystemInfo

from wish_command_execution.backend.base import Backend
from wish_command_execution.system_info import SystemInfoCollector
from wish_tools.tool_step_trace import main as step_trace

# ロギング設定
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

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

        # Check if the session is dead
        if self.interactive_session.is_dead:
            error_msg = "Error: Sliver session is in an invalid state. Cannot connect."
            print(error_msg, file=sys.stderr)
            sys.exit(1)

    async def execute_command(self, wish: Wish, command: str, cmd_num: int, log_files, timeout_sec: int) -> None:
        """Execute a command through Sliver C2.

        Args:
            wish: The wish to execute the command for.
            command: The command to execute.
            cmd_num: The command number.
            log_files: The log files to write output to.
            timeout_sec: The timeout in seconds for this command.
        """
        # Create command result
        result = CommandResult.create(cmd_num, command, log_files, timeout_sec)
        wish.command_results.append(result)

        try:
            # Connect to Sliver server first
            await self._connect()

            # Execute the command directly
            try:
                # Execute the command
                # Windowsシステムの場合、コマンドをcmd.exe経由で実行する
                os_type = self.interactive_session.os.lower()
                if "windows" in os_type:
                    # Windowsの場合、cmd.exeを使用して引数を正しく分割
                    # コマンドを分割
                    cmd_args = ["/C"] + command.split()
                    cmd_result = await self.interactive_session.execute("cmd.exe", cmd_args)
                else:
                    # Linux/macOSの場合は分割して実行
                    # 単純な分割（より複雑なケースでは改善が必要かもしれません）
                    cmd_parts = command.split()
                    cmd_name = cmd_parts[0]
                    cmd_args = cmd_parts[1:] if len(cmd_parts) > 1 else []
                    cmd_result = await self.interactive_session.execute(cmd_name, cmd_args)

                # Write results to log files
                with open(log_files.stdout, "w") as stdout_file, open(log_files.stderr, "w") as stderr_file:
                    if cmd_result.Stdout:
                        stdout_content = cmd_result.Stdout.decode('utf-8', errors='replace')
                        stdout_file.write(stdout_content)

                    if cmd_result.Stderr:
                        stderr_content = cmd_result.Stderr.decode('utf-8', errors='replace')
                        stderr_file.write(stderr_content)

                # Update command result
                exit_code = cmd_result.Status if cmd_result.Status is not None else 0
                
                # Mark the command as finished with exit code and add step trace
                await self.finish_with_trace(
                    wish=wish,
                    result=result,
                    exit_code=exit_code,
                    state=CommandState.SUCCESS if exit_code == 0 else CommandState.OTHERS,
                    trace_name="Command Execution Complete"
                )

                # Update the command result in the wish object
                for i, cmd_result in enumerate(wish.command_results):
                    if cmd_result.num == result.num:
                        wish.command_results[i] = result
                        break

            except Exception as e:
                # Handle errors
                with open(log_files.stderr, "w") as stderr_file:
                    error_msg = f"Sliver execution error: {str(e)}"
                    stderr_file.write(error_msg)
                await self._handle_command_failure(result, wish, 1, CommandState.OTHERS)

        except Exception as e:
            # Handle errors in the main thread
            with open(log_files.stderr, "w") as stderr_file:
                error_msg = f"Sliver execution error: {str(e)}"
                stderr_file.write(error_msg)
            await self._handle_command_failure(result, wish, 1, CommandState.OTHERS)

    async def _add_step_trace(self, wish: Wish, result: CommandResult, trace_name: str, exec_time_sec: float = 0):
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

            # Build trace message with the requested format
            trace_message = (
                f"# コマンド\n{result.command}\n\n"
                f"# タイムアウト [sec]\n{result.timeout_sec}\n\n"
                f"# 終了コード\n{result.exit_code if result.exit_code is not None else 'N/A'}\n\n"
                f"# 実行時間 [sec]\n{exec_time_sec:.2f}\n\n"
                f"# stdout\n{stdout_content}\n\n"
                f"# stderr\n{stderr_content}"
            )

            # デバッグログにも同じ内容を出力
            logger.debug(trace_message)

            # Send step trace
            step_trace(
                run_id=getattr(self, 'run_id', None) or wish.id,
                trace_name=trace_name,
                trace_message=trace_message
            )
        except Exception as e:
            print(f"Error adding step trace: {str(e)}")

    async def finish_with_trace(self, wish: Wish, result: CommandResult, exit_code: int, state: CommandState = None, trace_name: str = "Command Execution Complete", exec_time_sec: float = 0):
        """Finish command execution and send trace.
        
        Args:
            wish: The wish object.
            result: The command result.
            exit_code: The exit code of the command.
            state: The state of the command.
            trace_name: The name of the trace.
            exec_time_sec: The execution time in seconds.
        """
        # Finish the command
        result.finish(exit_code=exit_code, state=state)
        
        # Send trace
        await self._add_step_trace(wish, result, trace_name, exec_time_sec)

    async def _handle_command_failure(
        self, result: CommandResult, wish: Wish, exit_code: int, state: CommandState
    ):
        """Handle command failure.

        Args:
            result: The command result to update.
            wish: The wish associated with the command.
            exit_code: The exit code to set.
            state: The command state to set.
        """
        await self.finish_with_trace(
            wish=wish,
            result=result,
            exit_code=exit_code,
            state=state,
            trace_name="Command Execution Complete",
            exec_time_sec=0
        )
        
        # Update the command result in the wish object
        for i, cmd_result in enumerate(wish.command_results):
            if cmd_result.num == result.num:
                wish.command_results[i] = result
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
        # Find the command result
        result = None
        for cmd_result in wish.command_results:
            if cmd_result.num == cmd_num:
                result = cmd_result
                break

        if result and result.state == CommandState.DOING:
            # In the new async design, we don't have futures to cancel
            # We can only mark the command as cancelled in the result

            # Mark the command as cancelled and add step trace
            await self.finish_with_trace(
                wish=wish,
                result=result,
                exit_code=-1,  # Use -1 for cancelled commands
                state=CommandState.USER_CANCELLED,
                trace_name="Command Execution Complete"
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
