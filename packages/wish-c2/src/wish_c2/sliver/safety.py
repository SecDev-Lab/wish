"""Safe Sliver C2 connector with security features."""

import logging
import re
from collections.abc import Callable
from pathlib import Path

from ..exceptions import SecurityError
from ..models import CommandResult, FileTransferProgress, PortForward, ProcessInfo
from .connector import RealSliverConnector

logger = logging.getLogger(__name__)


class SafeSliverConnector(RealSliverConnector):
    """Sliver connector with safety features and restrictions."""

    # Dangerous command patterns
    DANGEROUS_PATTERNS = [
        r"rm\s+-rf\s+/",  # rm -rf /
        r":\(\)\s*\{.*\|.*&\s*\};",  # Fork bomb (include optional spaces)
        r"dd\s+if=/dev/zero",  # Disk wipe
        r"dd\s+of=/dev/[sh]d",  # Direct disk write
        r"mkfs\.",  # Format filesystem
        r">\s*/dev/sda",  # Direct disk write
        r"format\s+[cC]:",  # Windows format
        r"del\s+/[fF]\s+/[sS]\s+/[qQ]\s+[cC]:\\",  # Windows recursive delete
    ]

    # Write commands that modify the system
    WRITE_COMMANDS = {
        "rm",
        "rmdir",
        "mv",
        "cp",
        "mkdir",
        "touch",
        "chmod",
        "chown",
        "dd",
        "mkfs",
        "fdisk",
        "parted",
        "apt",
        "apt-get",
        "yum",
        "dnf",
        "pip",
        "npm",
        "gem",
        "systemctl",
        "service",
        "kill",
        "pkill",
        "reboot",
        "shutdown",
        "poweroff",
        "halt",
    }

    def __init__(self, config_path: Path, safety_config: dict, ssl_options: dict | None = None):
        """Initialize safe Sliver connector.

        Args:
            config_path: Path to Sliver client configuration
            safety_config: Safety configuration dictionary with:
                - sandbox_mode: Enable sandbox restrictions
                - read_only: Prevent write operations
                - allowed_commands: Whitelist of allowed commands
                - blocked_paths: List of paths to block access
                - max_file_size: Max file size for operations
            ssl_options: SSL configuration options (passed to parent)
        """
        super().__init__(config_path, ssl_options)
        self.sandbox_mode = safety_config.get("sandbox_mode", True)
        self.read_only = safety_config.get("read_only", False)
        self.allowed_commands = set(safety_config.get("allowed_commands", []))
        self.blocked_paths = set(safety_config.get("blocked_paths", []))
        self.max_file_size = safety_config.get("max_file_size", 10 * 1024 * 1024)  # 10MB default

        # Add default blocked paths
        self.blocked_paths.update(
            {
                "/etc/shadow",
                "/etc/passwd",
                "/etc/sudoers",
                "/root/.ssh",
                "/home/*/.ssh",
                r"C:\Windows\System32\config",
                r"C:\Users\*\NTUSER.DAT",
            }
        )

        logger.info(
            f"SafeSliverConnector initialized - "
            f"sandbox: {self.sandbox_mode}, "
            f"read_only: {self.read_only}, "
            f"allowed_commands: {len(self.allowed_commands)}"
        )

    async def execute_command(self, session_id: str, command: str) -> CommandResult:
        """Execute command with safety checks.

        Args:
            session_id: Session ID or name
            command: Command to execute

        Returns:
            Command result

        Raises:
            SecurityError: If command violates safety rules
        """
        # Perform safety checks
        self._validate_command_safety(command)

        # Check read-only mode
        if self.read_only and self._is_write_command(command):
            raise SecurityError(f"Write operations not allowed in read-only mode: {command}")

        # Check whitelist if configured
        if self.allowed_commands:
            base_cmd = command.split()[0] if command else ""
            if base_cmd not in self.allowed_commands:
                raise SecurityError(f"Command '{base_cmd}' not in allowed list")

        # Execute with parent class
        return await super().execute_command(session_id, command)

    def _validate_command_safety(self, command: str) -> None:
        """Validate command safety.

        Args:
            command: Command to validate

        Raises:
            SecurityError: If command is dangerous
        """
        if not self.sandbox_mode:
            return

        # Check dangerous patterns
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                raise SecurityError(f"Dangerous command pattern detected: {pattern}")

        # Check blocked paths
        for blocked_path in self.blocked_paths:
            # Simple string check for blocked paths
            # Remove trailing wildcards for base path check
            base_path = blocked_path.rstrip("*")
            if base_path in command:
                raise SecurityError(f"Access to blocked path '{blocked_path}' not allowed")

        # Check for command injection attempts
        if self._has_command_injection(command):
            raise SecurityError("Potential command injection detected")

    def _is_write_command(self, command: str) -> bool:
        """Check if command performs write operations.

        Args:
            command: Command to check

        Returns:
            True if command writes to system
        """
        if not command:
            return False

        # Check for output redirection
        if ">" in command or ">>" in command:
            return True

        # Check base command
        base_cmd = command.split()[0]
        return base_cmd in self.WRITE_COMMANDS

    def _has_command_injection(self, command: str) -> bool:
        """Check for command injection patterns.

        Args:
            command: Command to check

        Returns:
            True if injection patterns detected
        """
        # Common injection patterns
        injection_patterns = [
            r";\s*[a-zA-Z]",  # Command chaining with ;
            r"\|\s*[a-zA-Z]",  # Pipe to command
            r"&&\s*[a-zA-Z]",  # AND operator
            r"\|\|\s*[a-zA-Z]",  # OR operator
            r"`[^`]+`",  # Command substitution
            r"\$\([^)]+\)",  # Command substitution
            r"\$\{[^}]+\}",  # Variable expansion that might execute
        ]

        for pattern in injection_patterns:
            if re.search(pattern, command):
                # Allow some safe patterns
                if self._is_safe_pattern(command):
                    continue
                return True

        return False

    def _is_safe_pattern(self, command: str) -> bool:
        """Check if command contains known safe patterns.

        Args:
            command: Command to check

        Returns:
            True if pattern is known to be safe
        """
        # Safe patterns that might match injection patterns
        safe_patterns = [
            r"ps aux \| grep",  # Common process search
            r"netstat.*\| grep",  # Network connection search
            r"ls.*\| grep",  # File search
            r"cat.*\| grep",  # Content search
            r"echo \$[A-Z_]+",  # Environment variable echo
        ]

        for pattern in safe_patterns:
            if re.match(pattern, command):
                return True

        return False

    async def upload_file(
        self,
        session_id: str,
        local_path: Path,
        remote_path: str,
        progress_callback: Callable[[FileTransferProgress], None] | None = None,
    ) -> bool:
        """Upload file with safety checks.

        Args:
            session_id: Session ID
            local_path: Local file path
            remote_path: Remote destination path
            progress_callback: Optional progress callback

        Returns:
            True if successful

        Raises:
            SecurityError: If operation violates safety rules
        """
        if self.read_only:
            raise SecurityError("File upload not allowed in read-only mode")

        # Check file size
        if local_path.stat().st_size > self.max_file_size:
            raise SecurityError(f"File too large: {local_path} exceeds {self.max_file_size} bytes")

        # Check remote path
        for blocked_path in self.blocked_paths:
            if remote_path.startswith(blocked_path.rstrip("*")):
                raise SecurityError(f"Upload to blocked path not allowed: {remote_path}")

        # Call parent implementation
        return await super().upload_file(session_id, local_path, remote_path, progress_callback)

    async def download_file(
        self,
        session_id: str,
        remote_path: str,
        local_path: Path,
        progress_callback: Callable[[FileTransferProgress], None] | None = None,
    ) -> bool:
        """Download file with safety checks.

        Args:
            session_id: Session ID
            remote_path: Remote file path
            local_path: Local destination path
            progress_callback: Optional progress callback

        Returns:
            True if successful

        Raises:
            SecurityError: If operation violates safety rules
        """
        # Check remote path
        for blocked_path in self.blocked_paths:
            if remote_path.startswith(blocked_path.rstrip("*")):
                raise SecurityError(f"Download from blocked path not allowed: {remote_path}")

        # Call parent implementation
        return await super().download_file(session_id, remote_path, local_path, progress_callback)

    async def create_port_forward(
        self,
        session_id: str,
        local_port: int,
        remote_host: str,
        remote_port: int,
        local_host: str = "127.0.0.1",
    ) -> PortForward:
        """Create port forward with safety checks.

        Args:
            session_id: Session ID
            local_port: Local port to bind
            remote_host: Remote host
            remote_port: Remote port
            local_host: Local bind address

        Returns:
            Port forward information

        Raises:
            SecurityError: If operation violates safety rules
        """
        if self.read_only:
            raise SecurityError("Port forwarding not allowed in read-only mode")

        # Check if ports are in allowed range
        if hasattr(self, "allowed_ports") and self.allowed_ports:
            if local_port not in self.allowed_ports:
                raise SecurityError(f"Local port {local_port} not in allowed list")
            if remote_port not in self.allowed_ports:
                raise SecurityError(f"Remote port {remote_port} not in allowed list")

        # Check for privileged ports
        if local_port < 1024 and self.sandbox_mode:
            raise SecurityError("Cannot bind to privileged ports in sandbox mode")

        # Call parent implementation
        return await super().create_port_forward(session_id, local_port, remote_host, remote_port, local_host)

    async def kill_process(self, session_id: str, pid: int, force: bool = False) -> bool:
        """Kill process with safety checks.

        Args:
            session_id: Session ID
            pid: Process ID
            force: Force kill

        Returns:
            True if successful

        Raises:
            SecurityError: If operation violates safety rules
        """
        if self.read_only:
            raise SecurityError("Process termination not allowed in read-only mode")

        # Prevent killing system processes
        if pid <= 10 and self.sandbox_mode:
            raise SecurityError("Cannot kill system processes (PID <= 10) in sandbox mode")

        # If we have process info, check if it's a system process
        # This would require maintaining process list or checking before kill
        if hasattr(self, "_last_process_list"):
            for proc in self._last_process_list:
                if proc.pid == pid and proc.is_system_process:
                    raise SecurityError(f"Cannot kill system process: {proc.name}")

        # Call parent implementation
        return await super().kill_process(session_id, pid, force)

    async def get_processes(self, session_id: str) -> list[ProcessInfo]:
        """Get processes with caching for safety checks.

        Args:
            session_id: Session ID

        Returns:
            List of processes
        """
        processes = await super().get_processes(session_id)
        # Cache for safety checks
        self._last_process_list = processes
        return processes
