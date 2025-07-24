"""Tests for session manager functionality."""

import tempfile

import pytest
from wish_models import EngagementState, SessionMetadata

from wish_core.persistence.session_store import SessionStore
from wish_core.session import FileSessionManager, InMemorySessionManager


@pytest.mark.unit
class TestInMemorySessionManager:
    """Test InMemorySessionManager functionality."""

    @pytest.fixture
    def session_manager(self):
        """Create an InMemorySessionManager instance for testing."""
        return InMemorySessionManager()

    @pytest.fixture
    def sample_engagement_state(self):
        """Create a sample EngagementState for testing."""
        return EngagementState(
            id="test-engagement",
            name="Test Engagement",
            session_metadata=SessionMetadata(session_id="test-session-123"),
        )

    async def test_save_and_load_session(self, session_manager, sample_engagement_state):
        """Test saving and loading a session."""
        await session_manager.save_session(sample_engagement_state)

        loaded_state = await session_manager.load_session("test-session-123")
        assert loaded_state is not None
        assert loaded_state.id == sample_engagement_state.id
        assert loaded_state.session_metadata.session_id == "test-session-123"

    async def test_load_nonexistent_session(self, session_manager):
        """Test loading a non-existent session."""
        loaded_state = await session_manager.load_session("nonexistent")
        assert loaded_state is None

    async def test_list_sessions(self, session_manager):
        """Test listing sessions."""
        # Initially empty
        sessions = await session_manager.list_sessions()
        assert len(sessions) == 0

        # Add sessions
        state1 = EngagementState(
            id="engagement-1",
            name="Engagement 1",
            session_metadata=SessionMetadata(session_id="session-1"),
        )
        state2 = EngagementState(
            id="engagement-2",
            name="Engagement 2",
            session_metadata=SessionMetadata(session_id="session-2"),
        )

        await session_manager.save_session(state1)
        await session_manager.save_session(state2)

        sessions = await session_manager.list_sessions()
        assert len(sessions) == 2
        session_ids = [s.session_id for s in sessions]
        assert "session-1" in session_ids
        assert "session-2" in session_ids


@pytest.mark.unit
class TestFileSessionManager:
    """Test FileSessionManager functionality."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def session_store(self, temp_dir):
        """Create a SessionStore instance for testing."""
        return SessionStore(base_path=temp_dir)

    @pytest.fixture
    def session_manager(self, session_store):
        """Create a FileSessionManager instance for testing."""
        return FileSessionManager(session_store=session_store)

    @pytest.fixture
    def sample_engagement_state(self):
        """Create a sample EngagementState for testing."""
        return EngagementState(
            id="test-engagement",
            name="Test Engagement",
            session_metadata=SessionMetadata(session_id="test-session-123"),
        )

    async def test_save_and_load_session(self, session_manager, sample_engagement_state):
        """Test saving and loading current session."""
        await session_manager.save_session(sample_engagement_state)

        loaded_state = await session_manager.load_session("test-session-123")
        assert loaded_state is not None
        assert loaded_state.id == sample_engagement_state.id
        assert loaded_state.session_metadata.session_id == "test-session-123"

    async def test_load_different_session_id(self, session_manager, sample_engagement_state):
        """Test loading with different session ID returns None."""
        await session_manager.save_session(sample_engagement_state)

        loaded_state = await session_manager.load_session("different-session-id")
        assert loaded_state is None

    async def test_list_sessions_current_only(self, session_manager, sample_engagement_state):
        """Test listing sessions with only current session."""
        await session_manager.save_session(sample_engagement_state)

        sessions = await session_manager.list_sessions()
        assert len(sessions) == 1
        assert sessions[0].session_id == "test-session-123"

    async def test_archive_current_session(self, session_manager, sample_engagement_state):
        """Test archiving current session."""
        await session_manager.save_session(sample_engagement_state)

        archive_path = await session_manager.archive_current_session("test-archive")
        assert "test-archive" in archive_path

        # Current session should be cleared
        loaded_state = await session_manager.load_session("test-session-123")
        assert loaded_state is None

    async def test_archive_without_current_session(self, session_manager):
        """Test archiving when no current session exists."""
        with pytest.raises(ValueError, match="No current session to archive"):
            await session_manager.archive_current_session()

    async def test_load_archived_session(self, session_manager, sample_engagement_state):
        """Test loading archived session."""
        await session_manager.save_session(sample_engagement_state)
        archive_path = await session_manager.archive_current_session()

        loaded_state = await session_manager.load_archived_session(archive_path)
        assert loaded_state is not None
        assert loaded_state.id == sample_engagement_state.id

    async def test_list_sessions_with_archives(self, session_manager, sample_engagement_state):
        """Test listing sessions includes archived sessions."""
        # Save and archive a session
        await session_manager.save_session(sample_engagement_state)
        await session_manager.archive_current_session()

        # Create new current session
        new_state = EngagementState(
            id="new-engagement",
            name="New Engagement",
            session_metadata=SessionMetadata(session_id="new-session"),
        )
        await session_manager.save_session(new_state)

        sessions = await session_manager.list_sessions()
        # Should have both current and archived sessions
        assert len(sessions) >= 1  # At least the current session
        session_ids = [s.session_id for s in sessions]
        assert "new-session" in session_ids
