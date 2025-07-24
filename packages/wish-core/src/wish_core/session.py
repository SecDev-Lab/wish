"""Session management for wish-core."""

from abc import ABC, abstractmethod

from wish_models import EngagementState, SessionMetadata

from .persistence import SessionStore


class SessionManager(ABC):
    """Abstract session manager."""

    @abstractmethod
    async def save_session(self, state: EngagementState) -> None:
        """Save the current session state."""
        pass

    @abstractmethod
    async def load_session(self, session_id: str) -> EngagementState | None:
        """Load a session by ID."""
        pass

    @abstractmethod
    async def list_sessions(self) -> list[SessionMetadata]:
        """List all available sessions."""
        pass

    @abstractmethod
    def create_session(self) -> SessionMetadata:
        """Create a new session metadata."""
        pass

    @abstractmethod
    def get_current_directory(self) -> str:
        """Get current working directory."""
        pass


class InMemorySessionManager(SessionManager):
    """In-memory session manager for testing."""

    def __init__(self) -> None:
        self._sessions: dict[str, EngagementState] = {}

    async def save_session(self, state: EngagementState) -> None:
        """Save the current session state."""
        self._sessions[state.session_metadata.session_id] = state

    async def load_session(self, session_id: str) -> EngagementState | None:
        """Load a session by ID."""
        return self._sessions.get(session_id)

    async def list_sessions(self) -> list[SessionMetadata]:
        """List all available sessions."""
        return [state.session_metadata for state in self._sessions.values()]

    def create_session(self) -> SessionMetadata:
        """Create a new session metadata."""
        import uuid
        from datetime import datetime

        return SessionMetadata(
            session_id=str(uuid.uuid4()),
            engagement_name="Default Engagement",
            current_mode="recon",
            notes=None,
            total_commands=0,
            total_hosts_discovered=0,
            total_findings=0,
            session_start=datetime.now(),
            last_activity=datetime.now(),
        )

    def get_current_directory(self) -> str:
        """Get current working directory."""
        import os

        return os.getcwd()


class FileSessionManager(SessionManager):
    """File-based session manager using SessionStore."""

    def __init__(self, session_store: SessionStore) -> None:
        """Initialize file session manager.

        Args:
            session_store: SessionStore instance for persistence
        """
        self.session_store = session_store

    async def save_session(self, state: EngagementState) -> None:
        """Save the current session state to disk."""
        await self.session_store.save_current_session(state)

    async def load_session(self, session_id: str) -> EngagementState | None:
        """Load a session by ID.

        For file-based storage, this loads the current session if it exists.
        For archived sessions, use load_archived_session instead.
        """
        current_session = await self.session_store.load_current_session()
        if current_session and current_session.session_metadata.session_id == session_id:
            return current_session
        return None

    async def list_sessions(self) -> list[SessionMetadata]:
        """List all available sessions (current + archived)."""
        sessions = []

        # Add current session if it exists
        current_session = await self.session_store.load_current_session()
        if current_session:
            sessions.append(current_session.session_metadata)

        # Add archived sessions
        archived_sessions = await self.session_store.list_archived_sessions()
        for archived in archived_sessions:
            if archived.get("session_id"):
                from datetime import datetime

                created_at = archived.get("created_at")
                if created_at:
                    sessions.append(
                        SessionMetadata(
                            session_id=archived["session_id"],
                            session_start=datetime.fromisoformat(created_at),
                            last_activity=datetime.fromisoformat(created_at),
                            total_findings=archived.get("total_findings", 0),
                            current_mode=archived.get("current_mode", "recon"),
                            engagement_name=archived.get("engagement_name"),
                            notes=archived.get("notes"),
                            total_commands=archived.get("total_commands", 0),
                            total_hosts_discovered=archived.get("total_hosts_discovered", 0),
                        )
                    )

        return sessions

    async def load_archived_session(self, archive_path: str) -> EngagementState | None:
        """Load an archived session from file path."""
        return await self.session_store.load_archived_session(archive_path)

    async def archive_current_session(self, custom_name: str | None = None) -> str:
        """Archive the current session.

        Returns:
            Path to the archived session file
        """
        current_session = await self.session_store.load_current_session()
        if not current_session:
            raise ValueError("No current session to archive")

        return await self.session_store.archive_session(current_session, custom_name)

    def create_session(self) -> SessionMetadata:
        """Create a new session metadata."""
        import uuid
        from datetime import datetime

        return SessionMetadata(
            session_id=str(uuid.uuid4()),
            engagement_name="Default Engagement",
            current_mode="recon",
            notes=None,
            total_commands=0,
            total_hosts_discovered=0,
            total_findings=0,
            session_start=datetime.now(),
            last_activity=datetime.now(),
        )

    def get_current_directory(self) -> str:
        """Get current working directory."""
        import os

        return os.getcwd()
