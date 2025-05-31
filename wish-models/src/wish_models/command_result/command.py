"""Command model for representing commands with tool information."""

import json
from enum import Enum
from typing import Any, Dict, List

from pydantic import BaseModel


class CommandType(Enum):
    """Supported command execution tools."""

    BASH = "bash"
    MSFCONSOLE = "msfconsole"
    MSFCONSOLE_RESOURCE = "msfconsole_resource"
    METERPRETER = "meterpreter"
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

    @classmethod
    def create_msfconsole_resource_command(
        cls,
        commands: List[str],
        resource_file: str = "/tmp/msf_exploit.rc",
        **kwargs
    ) -> "Command":
        """Create an msfconsole resource file command.

        Args:
            commands: List of MSF commands to execute
            resource_file: Path to resource file
            **kwargs: Additional tool parameters

        Returns:
            Command configured for msfconsole resource execution.
        """
        # Create resource file content
        resource_content = '\n'.join(commands)
        bash_cmd = f"cat << 'EOF' > {resource_file}\n{resource_content}\nEOF\nmsfconsole -q -r {resource_file}"

        tool_parameters = {
            "resource_file": resource_file,
            "commands": commands,
            "timeout": 600,
            **kwargs
        }

        return cls(
            command=bash_cmd,
            tool_type=CommandType.MSFCONSOLE_RESOURCE,
            tool_parameters=tool_parameters
        )

    @classmethod
    def create_meterpreter_command(
        cls,
        command: str,
        session_id: str = "",
        **kwargs
    ) -> "Command":
        """Create a meterpreter session command.

        Args:
            command: The meterpreter command to execute
            session_id: Meterpreter session identifier
            **kwargs: Additional tool parameters

        Returns:
            Command configured for meterpreter execution.
        """
        tool_parameters = {
            "timeout": 300,
            **kwargs
        }
        if session_id:
            tool_parameters["session_id"] = session_id

        return cls(
            command=command,
            tool_type=CommandType.METERPRETER,
            tool_parameters=tool_parameters
        )

    @classmethod
    def create_python_command(
        cls,
        script_path: str,
        arguments: List[str] = None,
        **kwargs
    ) -> "Command":
        """Create a python command.

        Args:
            script_path: Path to Python script
            arguments: Script arguments
            **kwargs: Additional tool parameters

        Returns:
            Command configured for python execution.
        """
        if arguments is None:
            arguments = []

        args_str = ' '.join(f'"{arg}"' for arg in arguments)
        command = f"python3 {script_path} {args_str}".strip()

        tool_parameters = {
            "script_path": script_path,
            "arguments": arguments,
            "timeout": 300,
            **kwargs
        }

        return cls(
            command=command,
            tool_type=CommandType.PYTHON,
            tool_parameters=tool_parameters
        )

    @classmethod
    def create_powershell_command(
        cls,
        command: str,
        execution_policy: str = "Bypass",
        **kwargs
    ) -> "Command":
        """Create a PowerShell command.

        Args:
            command: The PowerShell command/script to execute
            execution_policy: PowerShell execution policy
            **kwargs: Additional tool parameters

        Returns:
            Command configured for PowerShell execution.
        """
        tool_parameters = {
            "execution_policy": execution_policy,
            "timeout": 300,
            **kwargs
        }

        return cls(
            command=command,
            tool_type=CommandType.POWERSHELL,
            tool_parameters=tool_parameters
        )

    def validate_tool_parameters(self) -> List[str]:
        """Validate tool parameters for the specified tool type.

        Returns:
            List of validation error messages.
        """
        errors = []

        if self.tool_type == CommandType.MSFCONSOLE:
            # MSFコマンドでexploit/を使う場合はRHOSTSが必要
            if 'use exploit/' in self.command:
                if not self.tool_parameters.get('rhosts'):
                    errors.append("RHOSTS parameter required for exploit modules")

            # Reverse payloadにはLHOSTが必要
            if any(payload in self.command.lower() for payload in ['reverse', 'bind']):
                if not self.tool_parameters.get('lhost'):
                    errors.append("LHOST parameter required for reverse/bind payloads")

        elif self.tool_type == CommandType.MSFCONSOLE_RESOURCE:
            if not self.tool_parameters.get('commands'):
                errors.append("Commands list required for resource file execution")

        elif self.tool_type == CommandType.PYTHON:
            if not self.tool_parameters.get('script_path'):
                errors.append("Script path required for Python execution")

        return errors

    @property
    def is_valid(self) -> bool:
        """Check if command is valid for its tool type."""
        return len(self.validate_tool_parameters()) == 0

    def get_execution_context(self) -> Dict[str, Any]:
        """Get execution context information for the command.

        Returns:
            Dictionary containing execution context details.
        """
        context = {
            "tool_type": self.tool_type.value,
            "requires_privileges": self._requires_privileges(),
            "estimated_duration": self._estimate_duration(),
            "risk_level": self._assess_risk_level(),
            "dependencies": self._get_dependencies()
        }
        return context

    def _requires_privileges(self) -> bool:
        """Check if command requires elevated privileges."""
        privileged_commands = ['sudo', 'su', 'chmod', 'chown', 'mount', 'systemctl']
        if self.tool_type == CommandType.BASH:
            return any(cmd in self.command.lower() for cmd in privileged_commands)
        elif self.tool_type == CommandType.MSFCONSOLE:
            return 'exploit' in self.command.lower()
        return False

    def _estimate_duration(self) -> int:
        """Estimate command execution duration in seconds."""
        if self.tool_type == CommandType.BASH:
            if 'nmap' in self.command:
                return 180  # nmap scans take time
            elif any(tool in self.command for tool in ['hydra', 'john', 'hashcat']):
                return 1800  # Password cracking tools
        elif self.tool_type == CommandType.MSFCONSOLE:
            return 60  # MSF commands typically quick
        elif self.tool_type == CommandType.MSFCONSOLE_RESOURCE:
            return 120  # Resource files may take longer

        return self.tool_parameters.get('timeout', 300)

    def _assess_risk_level(self) -> str:
        """Assess risk level of command execution."""
        high_risk_patterns = ['rm -rf', 'dd if=', 'mkfs', 'fdisk', 'exploit', 'payload']
        medium_risk_patterns = ['chmod', 'chown', 'sudo', 'su', 'mount']

        command_lower = self.command.lower()

        if any(pattern in command_lower for pattern in high_risk_patterns):
            return "HIGH"
        elif any(pattern in command_lower for pattern in medium_risk_patterns):
            return "MEDIUM"
        else:
            return "LOW"

    def _get_dependencies(self) -> List[str]:
        """Get list of command dependencies."""
        deps = []

        if self.tool_type in [CommandType.MSFCONSOLE, CommandType.MSFCONSOLE_RESOURCE]:
            deps.append("metasploit-framework")
        elif self.tool_type == CommandType.METERPRETER:
            deps.append("metasploit-framework")
        elif self.tool_type == CommandType.PYTHON:
            deps.append("python3")
        elif self.tool_type == CommandType.POWERSHELL:
            deps.append("powershell")

        # Tool-specific dependencies from command content
        if 'nmap' in self.command:
            deps.append("nmap")
        if 'hydra' in self.command:
            deps.append("hydra")
        if 'john' in self.command:
            deps.append("john")
        if 'hashcat' in self.command:
            deps.append("hashcat")

        return list(set(deps))  # Remove duplicates


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
