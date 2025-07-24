"""Base classes for C2 framework connectors."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from pathlib import Path

from .models import (
    CommandResult,
    DirectoryEntry,
    FileTransferProgress,
    ImplantConfig,
    ImplantInfo,
    InteractiveShell,
    PortForward,
    ProcessInfo,
    Screenshot,
    Session,
    StagerListener,
    StagingServer,
)


class BaseC2Connector(ABC):
    """Abstract base class for C2 framework connectors."""

    def __init__(self) -> None:
        """Initialize base connector."""
        self.connected: bool = False
        self.server: str = ""

    @abstractmethod
    async def connect(self) -> bool:
        """Connect to C2 server.

        Returns:
            bool: True if connection successful
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from C2 server."""
        pass

    @abstractmethod
    async def get_sessions(self) -> list[Session]:
        """Get list of active sessions.

        Returns:
            List of active sessions
        """
        pass

    @abstractmethod
    async def execute_command(self, session_id: str, command: str) -> CommandResult:
        """Execute command in a session.

        Args:
            session_id: Session identifier
            command: Command to execute

        Returns:
            Command execution result
        """
        pass

    @abstractmethod
    async def start_interactive_shell(self, session_id: str) -> InteractiveShell:
        """Start interactive shell session.

        Args:
            session_id: Session identifier

        Returns:
            Interactive shell instance
        """
        pass

    async def is_connected(self) -> bool:
        """Check if connected to C2 server.

        Returns:
            bool: True if connected
        """
        return self.connected

    async def get_server(self) -> str:
        """Get C2 server address.

        Returns:
            Server address string
        """
        return self.server

    # File operations
    async def upload_file(
        self,
        session_id: str,
        local_path: Path,
        remote_path: str,
        progress_callback: Callable[[FileTransferProgress], None] | None = None,
    ) -> bool:
        """Upload file to remote system.

        Args:
            session_id: Session identifier
            local_path: Local file path
            remote_path: Remote destination path
            progress_callback: Optional callback for progress updates

        Returns:
            True if successful

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("File upload not implemented")

    async def download_file(
        self,
        session_id: str,
        remote_path: str,
        local_path: Path,
        progress_callback: Callable[[FileTransferProgress], None] | None = None,
    ) -> bool:
        """Download file from remote system.

        Args:
            session_id: Session identifier
            remote_path: Remote file path
            local_path: Local destination path
            progress_callback: Optional callback for progress updates

        Returns:
            True if successful

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("File download not implemented")

    async def list_directory(self, session_id: str, path: str) -> list[DirectoryEntry]:
        """List directory contents.

        Args:
            session_id: Session identifier
            path: Directory path

        Returns:
            List of directory entries

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Directory listing not implemented")

    # Port forwarding
    async def create_port_forward(
        self,
        session_id: str,
        local_port: int,
        remote_host: str,
        remote_port: int,
        local_host: str = "127.0.0.1",
    ) -> PortForward:
        """Create port forward.

        Args:
            session_id: Session identifier
            local_port: Local port to bind
            remote_host: Remote host to forward to
            remote_port: Remote port to forward to
            local_host: Local host to bind (default: 127.0.0.1)

        Returns:
            Port forward information

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Port forwarding not implemented")

    async def list_port_forwards(self, session_id: str | None = None) -> list[PortForward]:
        """List active port forwards.

        Args:
            session_id: Optional session ID to filter by

        Returns:
            List of active port forwards

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Port forward listing not implemented")

    async def remove_port_forward(self, port_forward_id: str) -> bool:
        """Remove port forward.

        Args:
            port_forward_id: Port forward identifier

        Returns:
            True if successful

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Port forward removal not implemented")

    # Process management
    async def get_processes(self, session_id: str) -> list[ProcessInfo]:
        """Get process list from remote system.

        Args:
            session_id: Session identifier

        Returns:
            List of processes

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Process listing not implemented")

    async def kill_process(self, session_id: str, pid: int, force: bool = False) -> bool:
        """Kill a process on remote system.

        Args:
            session_id: Session identifier
            pid: Process ID to kill
            force: Force kill (SIGKILL vs SIGTERM)

        Returns:
            True if successful

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Process termination not implemented")

    # Screenshot
    async def take_screenshot(self, session_id: str, display: str = "") -> Screenshot:
        """Take screenshot of remote system.

        Args:
            session_id: Session identifier
            display: Display identifier (optional)

        Returns:
            Screenshot capture result

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Screenshot capture not implemented")

    # Implant management
    async def generate_implant(self, config: ImplantConfig) -> ImplantInfo:
        """Generate a new implant.

        Args:
            config: Implant configuration

        Returns:
            Generated implant information

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Implant generation not implemented")

    async def list_implants(self) -> list[ImplantInfo]:
        """List all generated implants.

        Returns:
            List of implant information

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Implant listing not implemented")

    async def delete_implant(self, implant_id: str) -> bool:
        """Delete a generated implant.

        Args:
            implant_id: Implant identifier

        Returns:
            True if successful

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Implant deletion not implemented")

    # Staging server management
    async def start_staging_server(
        self,
        host: str = "0.0.0.0",  # noqa: S104
        port: int | None = None,
        serve_path: str = ".",  # noqa: S104
    ) -> StagingServer:
        """Start implant staging server.

        Args:
            host: Bind address
            port: Bind port (if None, random port will be used)
            serve_path: Directory to serve

        Returns:
            Staging server information

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Staging server not implemented")

    async def stop_staging_server(self, server_id: str) -> bool:
        """Stop staging server.

        Args:
            server_id: Server identifier

        Returns:
            True if successful

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Staging server stop not implemented")

    async def list_staging_servers(self) -> list[StagingServer]:
        """List active staging servers.

        Returns:
            List of staging servers

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Staging server listing not implemented")

    # Stager management
    async def start_stager_listener(
        self, name: str, host: str, port: int | None = None, protocol: str = "http"
    ) -> tuple[StagerListener, str]:
        """Start stager listener and return stager code.

        Args:
            name: Stager name
            host: Host address
            port: Port number (if None, random port will be used)
            protocol: Protocol (http/https)

        Returns:
            Tuple of (StagerListener info, stager code)

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Stager listener not implemented")

    async def stop_stager_listener(self, listener_id: str) -> bool:
        """Stop stager listener.

        Args:
            listener_id: Listener ID

        Returns:
            True if successful

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Stager listener stop not implemented")

    async def list_stager_listeners(self) -> list[StagerListener]:
        """List active stager listeners.

        Returns:
            List of stager listeners

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Stager listener listing not implemented")
