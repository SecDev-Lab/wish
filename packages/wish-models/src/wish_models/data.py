"""
Collected data models for various tool outputs and artifacts.
"""

from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class CollectedData(BaseModel):
    """Important information such as collected credentials and files"""

    # Basic information
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier")
    type: Literal[
        "credentials", "hash", "file", "database", "config", "certificate", "api_key", "session_token", "other"
    ] = Field(description="Type of collected data")

    # Content
    content: str = Field(description="Collected content (passwords, hashes, etc.)")
    username: str | None = Field(None, description="Username (for credential data)")
    domain: str | None = Field(None, description="Domain")

    # Source information
    source_host_id: str | None = Field(None, description="Source host ID")
    source_service_id: str | None = Field(None, description="Source service ID")
    source_path: str | None = Field(None, description="Source path (file path, etc.)")

    # Discovery information
    discovered_by: str = Field(description="Tool or method used for collection")
    discovered_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Collection date and time")

    # Analysis status
    analyzed: bool = Field(False, description="Whether analyzed or not")
    working: bool = Field(False, description="Whether it's valid credentials or not")

    # Security
    is_sensitive: bool = Field(True, description="Sensitive information flag")
    notes: str | None = Field(None, description="Analysis notes")

    # Related data (relationships)
    source_finding_id: str | None = Field(None, description="Finding ID that led to this collected data")
    derived_finding_ids: list[str] = Field(
        default_factory=list, description="Finding IDs derived from this collected data"
    )

    def mark_as_working(self) -> None:
        """Mark as valid credentials"""
        self.working = True
        self.analyzed = True

    def mark_as_analyzed(self) -> None:
        """Mark as analyzed"""
        self.analyzed = True

    def link_source_finding(self, finding_id: str) -> None:
        """Link with source finding"""
        self.source_finding_id = finding_id

    def add_derived_finding(self, finding_id: str) -> None:
        """Add derived finding"""
        if finding_id not in self.derived_finding_ids:
            self.derived_finding_ids.append(finding_id)

    def is_credential(self) -> bool:
        """Determine if this is credential data"""
        return self.type == "credentials"

    def get_credential_summary(self) -> str:
        """Get credential summary"""
        if not self.is_credential():
            return "Not a credential"

        domain_part = f"@{self.domain}" if self.domain else ""
        username_part = self.username or "[unknown]"
        return f"{username_part}{domain_part}"

    model_config = ConfigDict()
