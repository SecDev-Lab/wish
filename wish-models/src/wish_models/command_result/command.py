"""Command model for representing commands with tool information."""

import json
from enum import Enum
from typing import Any, Dict

from pydantic import BaseModel


class CommandType(Enum):
    """Supported command execution tools."""
    
    BASH = "bash"
    MSFCONSOLE = "msfconsole"
    # Future extensions
    PYTHON = "python"
    POWERSHELL = "powershell"


class Command(BaseModel):
    """Represents a command with tool type and parameters."""
    
    command: str
    """The actual command string to execute."""
    
    tool_type: CommandType
    """The tool that should execute this command."""
    
    tool_parameters: Dict[str, Any] = {}
    """Tool-specific parameters for command execution."""
    
    def to_json(self) -> str:
        """Serialize Command to JSON string.
        
        Returns:
            JSON string representation of the Command.
        """
        return self.model_dump_json()
    
    @classmethod
    def from_json(cls, json_str: str) -> "Command":
        """Deserialize Command from JSON string.
        
        Args:
            json_str: JSON string representation of a Command.
            
        Returns:
            Command object.
            
        Raises:
            ValueError: If JSON is invalid or doesn't represent a valid Command.
        """
        return cls.model_validate_json(json_str)
    
    @classmethod
    def create_bash_command(
        cls, 
        command: str, 
        timeout: int = 300, 
        category: str = "",
        **kwargs
    ) -> "Command":
        """Create a bash command with standard parameters.
        
        Args:
            command: The bash command to execute.
            timeout: Command timeout in seconds.
            category: Command category hint (network, file, process, etc.).
            **kwargs: Additional tool parameters.
            
        Returns:
            Command configured for bash execution.
        """
        tool_parameters = {
            "timeout": timeout,
            **kwargs
        }
        if category:
            tool_parameters["category"] = category
            
        return cls(
            command=command,
            tool_type=CommandType.BASH,
            tool_parameters=tool_parameters
        )
    
    @classmethod
    def create_msfconsole_command(
        cls,
        command: str,
        module: str = "",
        rhosts: str = "",
        lhost: str = "",
        **kwargs
    ) -> "Command":
        """Create an msfconsole command with standard parameters.
        
        Args:
            command: The msfconsole command sequence to execute.
            module: The metasploit module path.
            rhosts: Target host(s).
            lhost: Local host for reverse connections.
            **kwargs: Additional tool parameters.
            
        Returns:
            Command configured for msfconsole execution.
        """
        tool_parameters = {**kwargs}
        if module:
            tool_parameters["module"] = module
        if rhosts:
            tool_parameters["rhosts"] = rhosts
        if lhost:
            tool_parameters["lhost"] = lhost
            
        return cls(
            command=command,
            tool_type=CommandType.MSFCONSOLE,
            tool_parameters=tool_parameters
        )


def parse_command_from_string(input_str: str) -> Command:
    """Parse command input from string (JSON or plain command).
    
    Args:
        input_str: Either a JSON string representing a Command or plain command string.
        
    Returns:
        Command object.
        
    Raises:
        ValueError: If input cannot be parsed as a valid command.
    """
    # Try to parse as JSON first
    try:
        data = json.loads(input_str)
        if isinstance(data, dict) and "command" in data and "tool_type" in data:
            return Command.model_validate(data)
    except (json.JSONDecodeError, ValueError):
        pass
    
    # If not JSON, treat as plain bash command
    return Command.create_bash_command(input_str)