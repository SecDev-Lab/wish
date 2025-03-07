"""Factory for CommandResult objects."""

import datetime
import os
import tempfile
from typing import Optional

import factory
from wish_models.command_result import CommandResult
from wish_models.command_result.command_state import CommandState
from wish_models.command_result.log_files import LogFiles


class LogFilesFactory(factory.Factory):
    """Factory for LogFiles objects."""

    class Meta:
        model = LogFiles

    stdout = factory.LazyFunction(lambda: tempfile.mkstemp(suffix=".stdout.log")[1])
    stderr = factory.LazyFunction(lambda: tempfile.mkstemp(suffix=".stderr.log")[1])

    @classmethod
    def create_with_content(cls, stdout_content: str = "", stderr_content: str = "") -> LogFiles:
        """Create LogFiles with actual files containing the given content.

        Args:
            stdout_content: Content to write to the stdout file.
            stderr_content: Content to write to the stderr file.

        Returns:
            LogFiles object with paths to the created files.
        """
        # Create temporary files for stdout and stderr
        stdout_fd, stdout_file = tempfile.mkstemp(suffix=".stdout.log")
        with os.fdopen(stdout_fd, "w") as f:
            f.write(stdout_content)

        stderr_fd, stderr_file = tempfile.mkstemp(suffix=".stderr.log")
        with os.fdopen(stderr_fd, "w") as f:
            f.write(stderr_content)

        return cls(stdout=stdout_file, stderr=stderr_file)


class CommandResultFactory(factory.Factory):
    """Factory for CommandResult objects."""

    class Meta:
        model = CommandResult

    num: int = factory.Sequence(lambda n: n)
    command: str = "echo 'Hello, World!'"
    exit_code: int = 0
    log_files: LogFiles = factory.SubFactory(LogFilesFactory)
    log_summary: Optional[str] = None
    state: CommandState = CommandState.SUCCESS
    created_at: datetime.datetime = factory.LazyFunction(datetime.datetime.now)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Create an instance of the model_class.

        This method is called by factory_boy to create an instance of the model_class.
        We override it to handle the case where log_files is None.
        """
        # If log_files is explicitly set to None, create a default LogFiles instance
        if 'log_files' in kwargs and kwargs['log_files'] is None:
            kwargs['log_files'] = LogFilesFactory()

        return super()._create(model_class, *args, **kwargs)

    @classmethod
    def create_success(cls, command: str = "echo 'Hello, World!'", stdout: str = "Hello, World!") -> CommandResult:
        """Create a successful CommandResult.

        Args:
            command: The command that was executed.
            stdout: The stdout content.

        Returns:
            CommandResult object representing a successful command execution.
        """
        log_files = LogFilesFactory.create_with_content(stdout_content=stdout)
        return cls(
            command=command,
            exit_code=0,
            log_files=log_files,
            state=CommandState.SUCCESS,
            log_summary=f"Command executed successfully: {stdout}"
        )

    @classmethod
    def create_command_not_found(cls, command: str = "unknown_command") -> CommandResult:
        """Create a CommandResult for a command not found error.

        Args:
            command: The command that was not found.

        Returns:
            CommandResult object representing a command not found error.
        """
        stderr = f"bash: {command}: command not found"
        log_files = LogFilesFactory.create_with_content(stderr_content=stderr)
        return cls(
            command=command,
            exit_code=127,
            log_files=log_files,
            state=CommandState.COMMAND_NOT_FOUND,
            log_summary=f"Command not found: {command}"
        )

    @classmethod
    def create_file_not_found(cls, command: str = "cat nonexistent.txt") -> CommandResult:
        """Create a CommandResult for a file not found error.

        Args:
            command: The command that resulted in a file not found error.

        Returns:
            CommandResult object representing a file not found error.
        """
        stderr = "cat: nonexistent.txt: No such file or directory"
        log_files = LogFilesFactory.create_with_content(stderr_content=stderr)
        return cls(
            command=command,
            exit_code=1,
            log_files=log_files,
            state=CommandState.FILE_NOT_FOUND,
            log_summary="File not found: nonexistent.txt"
        )

    @classmethod
    def create_with_log_files(cls, command: str, exit_code: int,
                             stdout_content: str = "", stderr_content: str = "",
                             state: CommandState = CommandState.SUCCESS,
                             log_summary: Optional[str] = None) -> CommandResult:
        """Create a CommandResult with log files containing the given content.

        Args:
            command: The command that was executed.
            exit_code: The exit code of the command.
            stdout_content: Content to write to the stdout file.
            stderr_content: Content to write to the stderr file.
            state: The state of the command.
            log_summary: The log summary.

        Returns:
            CommandResult object with log files containing the given content.
        """
        log_files = LogFilesFactory.create_with_content(
            stdout_content=stdout_content,
            stderr_content=stderr_content
        )
        return cls(
            command=command,
            exit_code=exit_code,
            log_files=log_files,
            state=state,
            log_summary=log_summary
        )
