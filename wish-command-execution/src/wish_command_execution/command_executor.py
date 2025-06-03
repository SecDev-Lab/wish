"""Command executor for wish-command-execution."""

import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
import asyncio
import time

from wish_models import CommandState, LogFiles, Wish, CommandResult
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
            # tool_typeとtool_parametersを取得
            tool_type = getattr(cmd_input, 'tool_type', None)
            tool_parameters = getattr(cmd_input, 'tool_parameters', None)
            
            # Debug logging
            logger.info(f"CommandInput attributes: {cmd_input.__dict__}")
            logger.info(f"tool_type from getattr: {tool_type}, tool_parameters: {tool_parameters}")
            
            await self.execute_command(wish, command, i, timeout_sec, tool_type, tool_parameters)

    async def execute_command(self, wish: Wish, command: str, cmd_num: int, timeout_sec: int, tool_type=None, tool_parameters=None) -> None:
        """Execute a single command for a wish.

        Args:
            wish: The wish to execute the command for.
            command: The command to execute.
            cmd_num: The command number.
            timeout_sec: The timeout in seconds for this command.
            tool_type: The type of tool to use (e.g., CommandType.MSFCONSOLE).
            tool_parameters: Tool-specific parameters.
        """
        # Create log directories and files
        log_dir = self.log_dir_creator(wish.id)
        stdout_path = log_dir / f"{cmd_num}.stdout"
        stderr_path = log_dir / f"{cmd_num}.stderr"
        log_files = LogFiles(stdout=stdout_path, stderr=stderr_path)

        # Check if we need to use a specific tool
        from wish_models.command_result.command import CommandType
        
        # Debug logging
        logger.info(f"Executing command with tool_type: {tool_type}, type: {type(tool_type)}")
        
        if tool_type and (tool_type == CommandType.MSFCONSOLE or str(tool_type).lower() == 'commandtype.msfconsole'):
            # Use MsfconsoleTool for msfconsole commands
            logger.info(f"Using MsfconsoleTool for command: {command}")
            await self._execute_with_msfconsole(wish, command, cmd_num, log_files, timeout_sec, tool_parameters)
        else:
            # Execute the command using the default backend (bash)
            logger.info(f"Using BashBackend for command: {command}")
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
    
    async def _execute_with_msfconsole(self, wish: Wish, command: str, cmd_num: int, log_files: LogFiles, timeout_sec: int, tool_parameters: Optional[Dict[str, Any]] = None) -> None:
        """Execute a command using MsfconsoleTool.
        
        Args:
            wish: The wish to execute the command for.
            command: The command to execute.
            cmd_num: The command number.
            log_files: The log files to write output to.
            timeout_sec: The timeout in seconds.
            tool_parameters: Tool-specific parameters.
        """
        from wish_tools.tools import MsfconsoleTool
        from wish_tools.framework.base import CommandInput as ToolCommandInput, ToolContext
        from wish_models.command_result.command import Command, CommandType
        
        # Create Command object
        command_obj = Command(
            command=command,
            tool_type=CommandType.MSFCONSOLE,
            tool_parameters=tool_parameters
        )
        
        # Create command result using the factory method
        result = CommandResult.create(
            num=cmd_num,
            command=command_obj,
            log_files=log_files,
            timeout_sec=timeout_sec
        )
        wish.command_results.append(result)
        
        # Initialize MsfconsoleTool
        tool = MsfconsoleTool()
        
        # Create tool command input
        logger.info(f"[CommandExecutor._execute_with_msfconsole] Creating ToolCommandInput with:")
        logger.info(f"  - command: {command}")
        logger.info(f"  - timeout_sec: {timeout_sec}")
        logger.info(f"  - tool_parameters: {tool_parameters}")
        
        tool_command = ToolCommandInput(
            command=command,
            timeout_sec=timeout_sec,
            tool_parameters=tool_parameters or {}
        )
        
        # Create tool context
        context = ToolContext(
            working_directory=".",
            environment={},
            timeout_override=timeout_sec
        )
        
        try:
            # Execute command with MsfconsoleTool
            start_time = time.time()
            tool_result = await tool.execute(tool_command, context)
            execution_time = time.time() - start_time
            
            # Ensure log directory exists
            log_files.stdout.parent.mkdir(parents=True, exist_ok=True)
            
            # Write output to log files (create empty file if no output)
            with open(log_files.stdout, 'w') as f:
                f.write(tool_result.output if tool_result.output else "")
            with open(log_files.stderr, 'w') as f:
                f.write(tool_result.error if tool_result.error else "")
            
            # Update command result
            exit_code = tool_result.exit_code if tool_result.exit_code is not None else (0 if tool_result.success else 1)
            state = CommandState.SUCCESS if tool_result.success else CommandState.OTHERS
            
            # Finish the command
            result.finish(exit_code=exit_code, state=state)
            
            # Add trace if backend supports it
            if hasattr(self.backend, '_add_step_trace'):
                await self.backend._add_step_trace(
                    wish=wish,
                    result=result,
                    trace_name="MsfConsole Command Execution Complete",
                    exec_time_sec=execution_time
                )
                
        except asyncio.TimeoutError:
            # Handle timeout
            result.finish(exit_code=124, state=CommandState.TIMEOUT)
            # Ensure log directory exists
            log_files.stdout.parent.mkdir(parents=True, exist_ok=True)
            with open(log_files.stdout, 'w') as f:
                f.write("")
            with open(log_files.stderr, 'w') as f:
                f.write("Command execution timed out")
                
        except Exception as e:
            # Handle other errors
            result.finish(exit_code=1, state=CommandState.OTHERS)
            # Ensure log directory exists
            log_files.stdout.parent.mkdir(parents=True, exist_ok=True)
            with open(log_files.stdout, 'w') as f:
                f.write("")
            with open(log_files.stderr, 'w') as f:
                f.write(f"Error executing msfconsole command: {str(e)}")
