from typing import Optional, Dict, Any
from pydantic import BaseModel
from wish_models.command_result.command import CommandType


class CommandInput(BaseModel):
    """Input for command execution."""

    command: str
    """Command to execute."""

    timeout_sec: int
    """Timeout for command execution in seconds."""
    
    tool_type: Optional[CommandType] = None
    """Type of tool to use for execution (e.g., bash, msfconsole)."""
    
    tool_parameters: Optional[Dict[str, Any]] = None
    """Tool-specific parameters for execution."""
