from pydantic import BaseModel


class CommandInput(BaseModel):
    """Input for command execution."""

    command: str
    """Command to execute."""

    timeout_sec: int
    """Timeout for command execution in seconds."""
