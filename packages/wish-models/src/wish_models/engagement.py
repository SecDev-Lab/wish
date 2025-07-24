"""
Engagement and target data models.
"""

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

if TYPE_CHECKING:
    from .data import CollectedData
    from .finding import Finding
    from .host import Host, Service
    from .session import SessionMetadata


class Target(BaseModel):
    """Definition of penetration test target"""

    # Basic information
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier")
    scope: str = Field(description="IP address, CIDR, domain, etc.")
    scope_type: Literal["ip", "cidr", "domain", "url"] = Field(description="Scope type")

    # Metadata
    name: str | None = Field(None, description="Target name (customer environment name, etc.)")
    description: str | None = Field(None, description="Target description")
    added_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Date and time added")

    # Constraints
    in_scope: bool = Field(True, description="Whether in scope or not")
    engagement_rules: str | None = Field(None, description="Engagement rules")

    @model_validator(mode="after")
    def validate_scope_consistency(self) -> "Target":
        """Validate consistency between scope type and scope value"""
        from .validation import validate_scope_type_and_value

        result = validate_scope_type_and_value(self.scope_type, self.scope)
        result.raise_if_invalid()
        return self

    @field_validator("added_at")
    @classmethod
    def validate_added_at_not_future(cls, v: datetime) -> datetime:
        """Validate that added date is not in the future"""
        from .validation import validate_datetime_not_future

        result = validate_datetime_not_future(v)
        return result.raise_if_invalid()

    model_config = ConfigDict()


class EngagementState(BaseModel):
    """Overall penetration test engagement state"""

    # Metadata
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique engagement identifier")
    name: str = Field(description="Engagement name")

    # Entity collections
    targets: dict[str, Target] = Field(default_factory=dict, description="Targets")
    hosts: dict[str, "Host"] = Field(default_factory=dict, description="Hosts")
    findings: dict[str, "Finding"] = Field(default_factory=dict, description="Findings")
    collected_data: dict[str, "CollectedData"] = Field(default_factory=dict, description="Collected data")

    # Session management
    session_metadata: "SessionMetadata" = Field(description="Session information")

    # State management
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Creation date and time")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Last update date and time")

    # Helper methods
    def get_active_hosts(self) -> list["Host"]:
        """Get list of active hosts"""
        return [host for host in self.hosts.values() if host.status == "up"]

    def get_open_services(self) -> list["Service"]:
        """Get list of open services"""
        services = []
        for host in self.hosts.values():
            services.extend([svc for svc in host.services if svc.state == "open"])
        return services

    def get_all_findings(self) -> list["Finding"]:
        """Get all findings"""
        return list(self.findings.values())

    def get_sensitive_collected_data(self) -> list["CollectedData"]:
        """Get sensitive collected data"""
        return [data for data in self.collected_data.values() if data.is_sensitive]

    def get_working_credentials(self) -> list["CollectedData"]:
        """Get valid credentials"""
        return [data for data in self.collected_data.values() if data.type == "credentials" and data.working]

    def update_timestamp(self) -> None:
        """Set update time to current time"""
        self.updated_at = datetime.now(UTC)
        self.session_metadata.update_activity()

    def get_current_mode(self) -> str:
        """Get current mode"""
        return self.session_metadata.current_mode

    def change_mode(self, new_mode: str) -> None:
        """Change mode"""
        self.session_metadata.change_mode(new_mode)
        self.update_timestamp()

    def add_command_to_history(self, command: str) -> None:
        """Add executed command to history"""
        self.session_metadata.add_command(command)
        self.update_timestamp()

    def add_target(self, target: Target) -> None:
        """Add a target to the engagement."""
        self.targets[target.id] = target
        self.update_timestamp()

    model_config = ConfigDict()
