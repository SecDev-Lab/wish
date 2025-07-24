"""Tests for session store functionality."""

import json
import tempfile
from pathlib import Path

import pytest
from wish_models import EngagementState, Finding, Host, SessionMetadata

from wish_core.persistence.session_store import SessionStore


@pytest.mark.unit
class TestSessionStore:
    """Test SessionStore functionality."""

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
    def sample_engagement_state(self):
        """Create a sample EngagementState for testing."""
        return EngagementState(
            id="test-engagement",
            name="Test Engagement",
            description="Test engagement for unit tests",
            session_metadata=SessionMetadata(session_id="test-session-123"),
        )

    async def test_save_and_load_current_session(self, session_store, sample_engagement_state):
        """Test saving and loading current session."""
        # Save session
        await session_store.save_current_session(sample_engagement_state)

        # Verify file was created
        assert session_store.current_session_file.exists()

        # Load session
        loaded_state = await session_store.load_current_session()
        assert loaded_state is not None
        assert loaded_state.id == sample_engagement_state.id
        assert loaded_state.name == sample_engagement_state.name
        assert loaded_state.session_metadata.session_id == sample_engagement_state.session_metadata.session_id

    async def test_load_nonexistent_session(self, session_store):
        """Test loading when no session file exists."""
        loaded_state = await session_store.load_current_session()
        assert loaded_state is None

    async def test_save_with_complex_data(self, session_store):
        """Test saving session with complex data structures."""

        # Create engagement with hosts and findings
        engagement = EngagementState(
            id="complex-test",
            name="Complex Test",
            session_metadata=SessionMetadata(session_id="complex-123"),
        )

        # Add host
        host = Host(
            id="192.168.1.100",
            ip_address="192.168.1.100",
            hostnames=["test-server"],
            os_info="Ubuntu 20.04",
            services=[],
            discovered_by="test",
        )
        engagement.hosts[host.id] = host

        # Add finding
        finding = Finding(
            id="finding-1",
            title="Open SSH Service",
            description="SSH service running on port 22",
            category="information_disclosure",
            severity="info",
            target_type="host",
            host_id=host.id,
            discovered_by="test",
        )
        engagement.findings[finding.id] = finding

        # Save and load
        await session_store.save_current_session(engagement)
        loaded_state = await session_store.load_current_session()

        assert loaded_state is not None
        assert len(loaded_state.hosts) == 1
        assert len(loaded_state.findings) == 1
        assert loaded_state.hosts["192.168.1.100"].hostnames == ["test-server"]
        assert loaded_state.findings["finding-1"].title == "Open SSH Service"

    async def test_archive_session(self, session_store, sample_engagement_state):
        """Test archiving a session."""
        # Save current session first
        await session_store.save_current_session(sample_engagement_state)

        # Archive it
        archive_path = await session_store.archive_session(sample_engagement_state, "test-archive")

        # Verify archive file was created
        assert Path(archive_path).exists()
        assert "test-archive" in archive_path

        # Verify current session was cleared
        assert not session_store.current_session_file.exists()

        # Verify archive contains correct data
        with open(archive_path) as f:
            archived_data = json.load(f)
        assert archived_data["id"] == sample_engagement_state.id
        assert "archived_at" in archived_data

    async def test_list_archived_sessions(self, session_store, sample_engagement_state):
        """Test listing archived sessions."""
        # Archive a session
        await session_store.archive_session(sample_engagement_state, "test-list")

        # List archives
        archives = await session_store.list_archived_sessions()

        assert len(archives) == 1
        assert archives[0]["engagement_name"] == sample_engagement_state.name
        assert archives[0]["session_id"] == sample_engagement_state.session_metadata.session_id

    async def test_load_archived_session(self, session_store, sample_engagement_state):
        """Test loading an archived session."""
        # Archive a session
        archive_path = await session_store.archive_session(sample_engagement_state)

        # Load from archive
        loaded_state = await session_store.load_archived_session(archive_path)

        assert loaded_state is not None
        assert loaded_state.id == sample_engagement_state.id
        assert loaded_state.name == sample_engagement_state.name

    async def test_cleanup_old_archives(self, session_store, sample_engagement_state):
        """Test cleanup of old archive files."""
        # Create multiple archive files
        for i in range(5):
            engagement = EngagementState(
                id=f"test-{i}",
                name=f"Test {i}",
                session_metadata=SessionMetadata(session_id=f"session-{i}"),
            )
            await session_store.archive_session(engagement, f"test-{i}")

        # Verify all archives exist
        archives_before = await session_store.list_archived_sessions()
        assert len(archives_before) == 5

        # Clean up with max_count=3
        await session_store.cleanup_old_archives(max_age_days=30, max_count=3)

        # Verify only 3 remain
        archives_after = await session_store.list_archived_sessions()
        assert len(archives_after) == 3

    async def test_corrupted_session_file_handling(self, session_store, temp_dir):
        """Test handling of corrupted session files."""
        # Create a corrupted session file
        session_store.current_session_file.write_text("invalid json content")

        # Try to load - should handle gracefully
        loaded_state = await session_store.load_current_session()
        assert loaded_state is None

        # Verify corrupted file was backed up
        corrupted_files = list(Path(temp_dir).glob("sessions/*.corrupted.*"))
        assert len(corrupted_files) == 1

    async def test_validate_session_data(self, session_store):
        """Test session data validation."""
        # Valid data
        valid_data = {
            "session_metadata": {},
            "targets": {},
            "hosts": {},
            "findings": {},
            "collected_data": {},
        }
        assert session_store._validate_session_data(valid_data)

        # Invalid data (missing required field)
        invalid_data = {
            "session_metadata": {},
            "targets": {},
            "hosts": {},
            # Missing 'findings'
        }
        assert not session_store._validate_session_data(invalid_data)
