"""Data models for C2 framework integration."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from .base import BaseC2Connector


class SessionStatus(str, Enum):
    """Session status enumeration."""

    ACTIVE = "active"
    STALE = "stale"
    DISCONNECTED = "disconnected"


class Session(BaseModel):
    """C2 session information."""

    id: str = Field(..., description="Session ID")
    name: str = Field(..., description="Session name (e.g., FANCY_TIGER)")
    host: str = Field(..., description="Target host")
    os: str = Field(..., description="Operating system")
    arch: str = Field(..., description="Architecture")
    user: str = Field(..., description="Current user")
    pid: int = Field(..., description="Process ID")
    status: SessionStatus = Field(..., description="Session status")
    last_checkin: datetime = Field(..., description="Last check-in time")


class InteractiveShell:
    """Interactive shell session manager."""

    def __init__(self, connector: "BaseC2Connector", session: Session):
        """Initialize interactive shell.

        Args:
            connector: C2 connector instance
            session: Session information
        """
        self.connector = connector
        self.session = session
        self.active = True
        # Generate shell prompt
        self.prompt = f"sliver ({session.name}) > "

    async def execute(self, command: str) -> str:
        """Execute command in shell.

        Args:
            command: Command to execute

        Returns:
            Command output
        """
        if not self.active:
            raise RuntimeError("Shell session is not active")

        result = await self.connector.execute_command(self.session.id, command)
        return result.stdout

    async def close(self) -> None:
        """Close shell session."""
        self.active = False

    async def exit(self) -> None:
        """Exit interactive shell (alias for close)."""
        await self.close()


class CommandResult(BaseModel):
    """Result of command execution."""

    stdout: str = Field(..., description="Standard output")
    stderr: str = Field("", description="Standard error output")
    exit_code: int = Field(..., description="Exit code")


class C2Config(BaseModel):
    """C2 connection configuration."""

    server: str = Field(..., description="C2 server address")
    port: int = Field(..., description="C2 server port")
    username: str | None = Field(None, description="Username for authentication")
    api_token: str | None = Field(None, description="API token for authentication")
    tls_enabled: bool = Field(True, description="Whether to use TLS")
    ca_cert_path: str | None = Field(None, description="CA certificate path")
    client_cert_path: str | None = Field(None, description="Client certificate path")
    client_key_path: str | None = Field(None, description="Client key path")


class FileTransferProgress(BaseModel):
    """File transfer progress information."""

    transfer_id: str = Field(..., description="Unique transfer ID")
    filename: str = Field(..., description="File name")
    total_bytes: int = Field(..., description="Total file size in bytes")
    transferred_bytes: int = Field(..., description="Bytes transferred so far")
    transfer_rate: float = Field(..., description="Transfer rate in bytes per second")
    is_upload: bool = Field(..., description="True for upload, False for download")
    started_at: datetime = Field(..., description="Transfer start time")
    estimated_completion: datetime | None = Field(None, description="Estimated completion time")

    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage."""
        if self.total_bytes == 0:
            return 0.0
        return (self.transferred_bytes / self.total_bytes) * 100

    @property
    def remaining_time_seconds(self) -> float | None:
        """Calculate estimated remaining time in seconds."""
        if self.transfer_rate == 0:
            return None
        remaining_bytes = self.total_bytes - self.transferred_bytes
        return remaining_bytes / self.transfer_rate


class PortForwardStatus(str, Enum):
    """Port forward status enumeration."""

    ACTIVE = "active"
    LISTENING = "listening"
    ERROR = "error"
    CLOSED = "closed"


class PortForward(BaseModel):
    """Port forwarding information."""

    id: str = Field(..., description="Unique port forward ID")
    session_id: str = Field(..., description="Associated session ID")
    local_host: str = Field("127.0.0.1", description="Local bind address")
    local_port: int = Field(..., description="Local port")
    remote_host: str = Field(..., description="Remote host")
    remote_port: int = Field(..., description="Remote port")
    status: PortForwardStatus = Field(..., description="Port forward status")
    created_at: datetime = Field(..., description="Creation time")
    bytes_sent: int = Field(0, description="Total bytes sent")
    bytes_received: int = Field(0, description="Total bytes received")
    active_connections: int = Field(0, description="Number of active connections")


class ProcessInfo(BaseModel):
    """Process information."""

    pid: int = Field(..., description="Process ID")
    ppid: int = Field(..., description="Parent process ID")
    name: str = Field(..., description="Process name")
    executable: str = Field(..., description="Executable path")
    owner: str = Field(..., description="Process owner/user")
    cpu_percent: float = Field(0.0, description="CPU usage percentage")
    memory_percent: float = Field(0.0, description="Memory usage percentage")
    memory_vms: int = Field(0, description="Virtual memory size in bytes")
    memory_rss: int = Field(0, description="Resident set size in bytes")
    created_at: datetime | None = Field(None, description="Process creation time")
    cmdline: list[str] = Field(default_factory=list, description="Command line arguments")
    status: str = Field("running", description="Process status")

    @property
    def is_system_process(self) -> bool:
        """Check if this is a system process."""
        # Common system process indicators
        system_names = {"systemd", "init", "kernel", "kthreadd", "System", "svchost.exe"}
        return self.name in system_names or self.pid <= 2


class Screenshot(BaseModel):
    """Screenshot capture result."""

    session_id: str = Field(..., description="Session ID that captured the screenshot")
    timestamp: datetime = Field(..., description="Capture timestamp")
    display: str = Field("", description="Display identifier (e.g., :0 on Linux)")
    resolution: tuple[int, int] = Field(..., description="Image resolution (width, height)")
    format: str = Field("png", description="Image format")
    size_bytes: int = Field(..., description="Image size in bytes")
    data: bytes = Field(..., description="Image data")

    class Config:
        """Pydantic configuration."""

        # Allow bytes field
        arbitrary_types_allowed = True


class DirectoryEntry(BaseModel):
    """Remote directory entry information."""

    name: str = Field(..., description="File/directory name")
    path: str = Field(..., description="Full path")
    size: int = Field(0, description="Size in bytes")
    mode: str = Field(..., description="File permissions")
    is_dir: bool = Field(..., description="True if directory")
    modified_at: datetime = Field(..., description="Last modification time")


class StagerListener(BaseModel):
    """Stager listener information."""

    id: str = Field(..., description="Listener ID")
    name: str = Field(..., description="Stager name")
    url: str = Field(..., description="Stager URL")
    host: str = Field(..., description="Host address")
    port: int = Field(8080, description="Port number")
    protocol: str = Field("http", description="Protocol (http/https)")
    status: str = Field("running", description="Listener status")
    started_at: datetime = Field(..., description="Start time")
    owner: str = Field("", description="File owner")
    group: str = Field("", description="File group")


class ImplantConfig(BaseModel):
    """Implant generation configuration."""

    name: str | None = Field(None, description="Implant name (auto-generated if not provided)")
    os: str = Field("linux", description="Target OS (linux, windows, darwin)")
    arch: str = Field("amd64", description="Target architecture (amd64, x86, arm64)")
    format: str = Field("exe", description="Output format (exe, shellcode, shared, service)")
    protocol: str = Field("https", description="C2 protocol (https, http, tcp, dns)")
    callback_host: str = Field(..., description="C2 callback host/IP")
    callback_port: int = Field(443, description="C2 callback port")
    skip_symbols: bool = Field(True, description="Skip debug symbols")
    obfuscate: bool = Field(True, description="Enable obfuscation")
    timeout: int = Field(60, description="Connection timeout in seconds")
    reconnect_interval: int = Field(60, description="Reconnect interval in seconds")
    max_connection_errors: int = Field(10, description="Max connection errors before giving up")


class ImplantInfo(BaseModel):
    """Generated implant information."""

    id: str = Field(..., description="Implant ID")
    name: str = Field(..., description="Implant name")
    file_path: str = Field(..., description="Path to generated implant file")
    size: int = Field(..., description="File size in bytes")
    hash_sha256: str = Field(..., description="SHA256 hash of implant")
    config: ImplantConfig = Field(..., description="Configuration used to generate implant")
    generated_at: datetime = Field(..., description="Generation timestamp")


class StagingServer(BaseModel):
    """Implant staging server information."""

    id: str = Field(..., description="Server ID")
    protocol: str = Field("http", description="Protocol (http/https)")
    host: str = Field(..., description="Bind address")
    port: int = Field(..., description="Bind port")
    serving_path: str = Field(..., description="Path serving implants")
    implant_urls: dict[str, str] = Field(default_factory=dict, description="Map of implant name to URL")
    started_at: datetime = Field(..., description="Start timestamp")
    status: str = Field("running", description="Server status")


class StagerDownload(BaseModel):
    """Active stager download information."""

    id: str = Field(..., description="Download ID")
    client: str = Field(..., description="Client IP address")
    implant: str = Field(..., description="Implant name")
    size: int = Field(..., description="Total size in bytes")
    transferred: int = Field(0, description="Bytes transferred")
    started: datetime = Field(..., description="Download start time")
    status: str = Field("downloading", description="Download status")
    listener_id: str = Field(..., description="Associated listener ID")
