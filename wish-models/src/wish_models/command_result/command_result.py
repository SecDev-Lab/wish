import json

from pydantic import BaseModel

from wish_models.command_result.command_state import CommandState
from wish_models.command_result.log_files import LogFiles
from wish_models.utc_datetime import UtcDatetime


class CommandResult(BaseModel):
    """Result of a command."""

    num: int
    """Sequence number of the command in a wish.

    It starts from 1."""

    command: str
    """Command executed."""

    state: CommandState
    """Status of the command."""

    timeout_sec: int | None = None
    """Timeout for command execution in seconds.

    For wish, it's always None."""

    exit_code: int | None = None
    """Exit code of the command.

    It's None before the command is finished."""

    log_summary: str | None = None
    """Summary of the command execution log.

    It's None before the command is finished."""

    log_files: LogFiles
    """Paths to log files of the command execution."""

    created_at: UtcDatetime
    """Time when the command was created.

    It's the same as the time when the wish was created.
    """

    finished_at: UtcDatetime | None = None
    """Time when the command was finished.

    It's None before the command is finished."""

    @classmethod
    def create(cls, num: int, command: str, log_files: LogFiles) -> "CommandResult":
        return cls(
            num=num,
            command=command,
            state=CommandState.DOING,
            log_files=log_files,
            created_at=UtcDatetime.now(),
        )

    @classmethod
    def from_json(cls, command_result_json: str) -> "CommandResult":
        return cls.model_validate_json(command_result_json)

    @classmethod
    def from_dict(cls, command_result_dict: dict) -> "CommandResult":
        return cls.model_validate(command_result_dict)

    def to_json(self) -> str:
        return self.model_dump_json(indent=2)

    def to_dict(self) -> dict:
        return self.model_dump()

    def finish(self, exit_code: int, state: CommandState | None = None, log_summary: str | None = None) -> None:
        """Mark the command as finished and update its state.

        Args:
            exit_code: The exit code of the command.
            state: The state of the command. If None, it will be determined by wish-log-analysis.
            log_summary: Optional summary of the command execution log.
                If None, log_summary will remain None and will be set by wish-log-analysis.
        """
        self.exit_code = exit_code
        if state is not None:
            self.state = state
        if log_summary is not None:
            self.log_summary = log_summary
        self.finished_at = UtcDatetime.now()


def parse_command_results_json(command_results_json: str) -> list[CommandResult]:
    """Parse JSON string to list of CommandResult."""
    command_result_dicts = json.loads(command_results_json)
    return [CommandResult.from_dict(command_result_dict) for command_result_dict in command_result_dicts]
