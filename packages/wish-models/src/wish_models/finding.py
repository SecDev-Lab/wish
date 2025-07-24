"""
Finding data models for security discoveries.
"""

from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Finding(BaseModel):
    """Security vulnerabilities and findings"""

    # Basic information
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier")
    title: str = Field(description="Finding title")
    description: str = Field(description="Detailed description")

    # Classification
    category: Literal[
        "vulnerability",
        "misconfiguration",
        "information_disclosure",
        "weak_authentication",
        "encryption_issue",
        "other",
    ] = Field(description="Finding category")

    severity: Literal["info", "low", "medium", "high", "critical"] = Field("info", description="Severity level")

    # Target information
    target_type: Literal["host", "service", "application", "network"] = Field(description="Target type")
    host_id: str | None = Field(None, description="Related host ID")
    service_id: str | None = Field(None, description="Related service ID")
    url: str | None = Field(None, description="Related URL")

    # Technical details
    cve_ids: list[str] = Field(default_factory=list, description="Related CVE IDs")
    evidence: str | None = Field(None, description="Evidence (screenshots, logs, etc.)")

    # Discovery information
    discovered_by: str = Field(description="Tool used for discovery")
    discovered_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Discovery date and time")

    # Response status
    status: Literal["new", "investigating", "confirmed", "false_positive", "resolved"] = Field(
        "new", description="Response status"
    )

    # Recommendations
    recommendation: str | None = Field(None, description="Remediation recommendations")
    references: list[str] = Field(default_factory=list, description="Reference URLs")

    # Related data (relationships)
    related_collected_data_ids: list[str] = Field(default_factory=list, description="Related collected data IDs")

    def mark_verified(self) -> None:
        """Mark finding as verified"""
        self.status = "confirmed"

    def mark_false_positive(self) -> None:
        """Mark finding as false positive"""
        self.status = "false_positive"

    def add_reference(self, reference: str) -> None:
        """Add reference URL or citation"""
        if reference not in self.references:
            self.references.append(reference)

    def add_cve(self, cve_id: str) -> None:
        """Add CVE ID (preventing duplicates)"""
        from .validation import validate_cve_id

        result = validate_cve_id(cve_id)
        result.raise_if_invalid()

        if cve_id not in self.cve_ids:
            self.cve_ids.append(cve_id)

    def link_collected_data(self, data_id: str) -> None:
        """Add relationship with collected data"""
        if data_id not in self.related_collected_data_ids:
            self.related_collected_data_ids.append(data_id)

    def is_critical(self) -> bool:
        """Determine if this is a critical finding"""
        return self.severity in ["critical", "high"]

    @field_validator("cve_ids")
    @classmethod
    def validate_cve_format(cls, v: list[str]) -> list[str]:
        """Validate CVE ID format"""
        from .validation import validate_cve_id

        for cve_id in v:
            result = validate_cve_id(cve_id)
            result.raise_if_invalid()
        return v

    @field_validator("url")
    @classmethod
    def validate_url_format(cls, v: str | None) -> str | None:
        """Validate URL format"""
        if v is None:
            return v
        from .validation import validate_url

        result = validate_url(v)
        return result.raise_if_invalid()

    @field_validator("discovered_at")
    @classmethod
    def validate_discovered_at_not_future(cls, v: datetime) -> datetime:
        """Validate that discovery date is not in the future"""
        from .validation import validate_datetime_not_future

        result = validate_datetime_not_future(v)
        return result.raise_if_invalid()

    model_config = ConfigDict()
