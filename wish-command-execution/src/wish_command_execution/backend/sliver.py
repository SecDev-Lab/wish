"""Sliver C2 backend for command execution."""

import asyncio
from typing import Dict, Tuple, Any, Optional

from wish_models import CommandResult, CommandState, Wish
from sliver import SliverClient, SliverClientConfig

from wish_command_execution.backend.base import Backend


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
        self.running_commands: Dict[int, Tuple[asyncio.Task, CommandResult, Wish]] = {}  # Track running commands

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

        with open(log_files.stdout, "w") as stdout_file, open(log_files.stderr, "w") as stderr_file:
            try:
                # Run the async command in a separate thread with its own event loop
                import threading
                
                def run_async_command():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(self._execute_command_wrapper(command, stdout_file, stderr_file, result, wish, cmd_num))
                    except Exception as e:
                        # Handle errors in the thread
                        error_msg = f"Sliver execution error in thread: {str(e)}"
                        stderr_file.write(error_msg)
                        self._handle_command_failure(result, wish, 1, CommandState.OTHERS)
                    finally:
                        loop.close()
                
                # Start the thread
                thread = threading.Thread(target=run_async_command)
                thread.daemon = True  # Make thread daemon so it doesn't block program exit
                thread.start()
                
                # Return immediately for UI (non-blocking)
                return
                
            except Exception as e:
                # Handle errors in the main thread
                error_msg = f"Sliver execution error: {str(e)}"
                stderr_file.write(error_msg)
                self._handle_command_failure(result, wish, 1, CommandState.OTHERS)

    async def _execute_command_wrapper(self, command, stdout_file, stderr_file, result, wish, cmd_num):
        """Wrapper to execute a command and handle its lifecycle.
        
        Args:
            command: The command to execute.
            stdout_file: File to write stdout to.
            stderr_file: File to write stderr to.
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
            if cmd_result.Stdout:
                stdout_file.write(cmd_result.Stdout.decode('utf-8', errors='replace'))
            if cmd_result.Stderr:
                stderr_file.write(cmd_result.Stderr.decode('utf-8', errors='replace'))
            
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
        # This is handled differently in the Sliver backend
        # Commands are executed synchronously in _execute_command_wrapper
        pass

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
