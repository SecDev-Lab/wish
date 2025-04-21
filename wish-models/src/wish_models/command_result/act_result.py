"""ActResult class for command generation API."""

from pydantic import BaseModel


class ActResult(BaseModel):
    """Result of a command execution for Act mode.

    This is a simplified version of CommandResult used specifically for the command generation API.
    """

    command: str
    """Command executed."""

    exit_class: str
    """Status of the command (SUCCESS, TIMEOUT, NETWORK_ERROR, etc.)."""

    exit_code: str
    """Exit code of the command."""

    log_summary: str
    """Summary of the command execution log."""

    @classmethod
    def from_dict(cls, act_result_dict: dict) -> "ActResult":
        """Create an ActResult from a dictionary."""
        return cls.model_validate(act_result_dict)

    def model_dump(self) -> dict:
        """Convert the ActResult to a dictionary."""
        return super().model_dump()
