from pydantic import BaseModel


class CommandInput(BaseModel):
    """Input for command execution."""

    command: str
    """Command to execute."""

    timeout_sec: int | None
    """Timeout for command execution in seconds."""
