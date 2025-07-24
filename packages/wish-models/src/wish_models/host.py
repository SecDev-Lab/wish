"""
Host and service data models.
"""

from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SMBShare(BaseModel):
    """SMB share information"""

    name: str = Field(description="Share name")
    type: str = Field(description="Share type (Disk, IPC, etc.)")
    comment: str = Field(default="", description="Share comment")
    accessible: bool | None = Field(None, description="Whether accessible")
    writable: bool | None = Field(None, description="Whether writable")
    discovered_by: str = Field(description="Tool used for discovery")
    discovered_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Discovery date and time")


class SMBInfo(BaseModel):
    """SMB/NetBIOS service information"""

    # Basic information
    workgroup: str | None = Field(None, description="Workgroup name")
    domain: str | None = Field(None, description="Domain name")
    server_name: str | None = Field(None, description="Server name")

    # OS information
    os_name: str | None = Field(None, description="OS name")
    os_version: str | None = Field(None, description="OS version")

    # Share information
    shares: list[SMBShare] = Field(default_factory=list, description="SMB share list")

    # Access information
    anonymous_access: bool = Field(False, description="Anonymous access allowed")
    null_session: bool = Field(False, description="NULL session allowed")

    # Discovery information
    discovered_by: str = Field(description="Tool used for discovery")
    discovered_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Discovery date and time")


class Service(BaseModel):
    """Service running on a host"""

    # Basic information
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier")
    host_id: str = Field(description="ID of the host this service belongs to")
    port: int = Field(description="Port number")
    protocol: Literal["tcp", "udp"] = Field(description="Protocol")

    # Service information
    service_name: str | None = Field(None, description="Service name (http, ssh, etc.)")
    product: str | None = Field(None, description="Product name (Apache, OpenSSH, etc.)")
    version: str | None = Field(None, description="Version information")
    extrainfo: str | None = Field(None, description="Additional information")

    # State
    state: Literal["open", "closed", "filtered"] = Field(description="Port state")
    confidence: float | None = Field(None, description="Service identification confidence (0-1)")

    # Discovery information
    discovered_by: str = Field(description="Tool used for discovery")
    discovered_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Discovery date and time")

    # Security related
    banner: str | None = Field(None, description="Banner information")
    ssl_info: dict[str, Any] | None = Field(None, description="SSL/TLS information")

    @field_validator("port")
    @classmethod
    def validate_port_range(cls, v: int) -> int:
        """Validate port number range"""
        from .validation import validate_port

        result = validate_port(v)
        return result.raise_if_invalid()

    @field_validator("confidence")
    @classmethod
    def validate_confidence_range(cls, v: float | None) -> float | None:
        """Validate confidence score range"""
        from .validation import validate_confidence_score

        result = validate_confidence_score(v)
        return result.raise_if_invalid()

    @field_validator("discovered_at")
    @classmethod
    def validate_discovered_at_not_future(cls, v: datetime) -> datetime:
        """Validate that discovery date is not in the future"""
        from .validation import validate_datetime_not_future

        result = validate_datetime_not_future(v)
        return result.raise_if_invalid()

    model_config = ConfigDict()


class Host(BaseModel):
    """Information about discovered hosts"""

    # Basic information
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier")
    ip_address: str = Field(description="IP address")
    hostnames: list[str] = Field(default_factory=list, description="List of hostnames")

    # State information
    status: Literal["up", "down", "unknown"] = Field("unknown", description="Host status")
    os_info: str | None = Field(None, description="OS information")
    os_confidence: float | None = Field(None, description="OS detection confidence (0-1)")

    # Network information
    mac_address: str | None = Field(None, description="MAC address")
    services: list[Service] = Field(default_factory=list, description="Discovered services")

    # Service-specific information
    smb_info: SMBInfo | None = Field(None, description="SMB/NetBIOS service information")

    # Discovery information
    discovered_by: str = Field(description="Tool or method used for discovery")
    discovered_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Discovery date and time")
    last_seen: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Last seen date and time")

    # Additional metadata
    tags: list[str] = Field(default_factory=list, description="Tags (DMZ, internal network, etc.)")
    notes: str | None = Field(None, description="Manually added notes")

    @field_validator("ip_address")
    @classmethod
    def validate_ip_format(cls, v: str) -> str:
        """Validate IP address format"""
        from .validation import validate_ip_address

        result = validate_ip_address(v)
        return result.raise_if_invalid()

    @field_validator("mac_address")
    @classmethod
    def validate_mac_format(cls, v: str | None) -> str | None:
        """Validate MAC address format"""
        from .validation import validate_mac_address

        result = validate_mac_address(v)
        return result.raise_if_invalid()

    @field_validator("os_confidence")
    @classmethod
    def validate_os_confidence_range(cls, v: float | None) -> float | None:
        """Validate OS confidence score range"""
        from .validation import validate_confidence_score

        result = validate_confidence_score(v)
        return result.raise_if_invalid()

    @field_validator("discovered_at", "last_seen")
    @classmethod
    def validate_datetime_not_future(cls, v: datetime) -> datetime:
        """Validate that date is not in the future"""
        from .validation import validate_datetime_not_future

        result = validate_datetime_not_future(v)
        return result.raise_if_invalid()

    def add_service(self, service: Service) -> None:
        """Add or update service"""
        # Check for existing service (same port/protocol)
        for existing_service in self.services:
            if existing_service.port == service.port and existing_service.protocol == service.protocol:
                # Update existing service
                existing_service.service_name = service.service_name or existing_service.service_name
                existing_service.product = service.product or existing_service.product
                existing_service.version = service.version or existing_service.version
                existing_service.extrainfo = service.extrainfo or existing_service.extrainfo
                existing_service.banner = service.banner or existing_service.banner
                existing_service.ssl_info = service.ssl_info or existing_service.ssl_info
                existing_service.state = service.state
                existing_service.confidence = service.confidence or existing_service.confidence
                return

        # Add new service
        service.host_id = self.id
        self.services.append(service)

    def update_last_seen(self) -> None:
        """Update last seen time"""
        self.last_seen = datetime.now(UTC)

    def add_hostname(self, hostname: str) -> None:
        """Add hostname (preventing duplicates)"""
        if hostname not in self.hostnames:
            self.hostnames.append(hostname)

    def add_tag(self, tag: str) -> None:
        """Add tag (preventing duplicates)"""
        if tag not in self.tags:
            self.tags.append(tag)

    def get_open_ports(self) -> list[int]:
        """Get list of open ports"""
        return [svc.port for svc in self.services if svc.state == "open"]

    model_config = ConfigDict()
