"""
Session metadata and management models.
"""

from datetime import UTC, datetime
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class SessionMetadata(BaseModel):
    """Lightweight session management information"""

    # Basic session information
    session_id: str = Field(default_factory=lambda: str(uuid4()), description="Session identifier")
    engagement_name: str | None = Field(None, description="Engagement name")

    # Current state
    current_mode: str = Field("recon", description="Current mode (recon/enum/exploit etc.)")
    session_start: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Session start time")
    last_activity: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Last activity time")

    # Execution history (lightweight)
    command_history: list[str] = Field(default_factory=list, description="Command execution history")
    mode_history: list[tuple[str, datetime]] = Field(default_factory=list, description="Mode change history")

    # Metadata
    notes: str | None = Field(None, description="Session notes")
    tags: list[str] = Field(default_factory=list, description="Session tags")

    # Statistics
    total_commands: int = Field(0, description="Total number of executed commands")
    total_hosts_discovered: int = Field(0, description="Number of discovered hosts")
    total_findings: int = Field(0, description="Total number of findings")

    def update_activity(self) -> None:
        """Update last activity time"""
        self.last_activity = datetime.now(UTC)

    def add_command(self, command: str) -> None:
        """Add to command history (keep only latest 100)"""
        self.command_history.append(command)
        if len(self.command_history) > 100:
            self.command_history = self.command_history[-100:]
        self.total_commands += 1
        self.update_activity()

    def change_mode(self, new_mode: str) -> None:
        """Change mode and record history"""
        self.mode_history.append((self.current_mode, datetime.now(UTC)))
        self.current_mode = new_mode
        self.update_activity()

    def add_tag(self, tag: str) -> None:
        """Add tag (preventing duplicates)"""
        if tag not in self.tags:
            self.tags.append(tag)

    def get_session_duration(self) -> float:
        """Get session duration in seconds"""
        return (self.last_activity - self.session_start).total_seconds()

    model_config = ConfigDict()
