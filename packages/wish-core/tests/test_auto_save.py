"""Tests for auto-save functionality."""

import asyncio
import tempfile

import pytest
from wish_models import EngagementState, SessionMetadata

from wish_core.persistence.auto_save import AutoSaveManager
from wish_core.persistence.session_store import SessionStore


@pytest.mark.unit
class TestAutoSaveManager:
    """Test AutoSaveManager functionality."""

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
            session_metadata=SessionMetadata(session_id="test-session"),
        )

    @pytest.fixture
    def auto_save_manager(self, session_store, sample_engagement_state):
        """Create an AutoSaveManager instance for testing."""

        def state_provider():
            return sample_engagement_state

        return AutoSaveManager(
            session_store=session_store,
            save_interval=1,  # Short interval for testing
            state_provider=state_provider,
        )

    async def test_start_stop_auto_save(self, auto_save_manager):
        """Test starting and stopping auto-save."""
        assert not auto_save_manager.is_running

        await auto_save_manager.start_auto_save()
        assert auto_save_manager.is_running

        await auto_save_manager.stop_auto_save()
        assert not auto_save_manager.is_running

    async def test_mark_changes(self, auto_save_manager):
        """Test marking changes."""
        assert not auto_save_manager.has_unsaved_changes

        auto_save_manager.mark_changes()
        assert auto_save_manager.has_unsaved_changes

    async def test_force_save(self, auto_save_manager, session_store):
        """Test force save functionality."""
        auto_save_manager.mark_changes()

        success = await auto_save_manager.force_save()
        assert success
        assert not auto_save_manager.has_unsaved_changes

        # Verify file was saved
        assert session_store.current_session_file.exists()

    async def test_force_save_without_state_provider(self, session_store):
        """Test force save without state provider."""
        auto_save_manager = AutoSaveManager(session_store=session_store)

        success = await auto_save_manager.force_save()
        assert not success

    async def test_auto_save_loop(self, auto_save_manager, session_store):
        """Test the auto-save loop functionality."""
        # Mark changes and start auto-save
        auto_save_manager.mark_changes()
        await auto_save_manager.start_auto_save()

        # Wait for auto-save to trigger
        await asyncio.sleep(1.5)  # Wait longer than save_interval

        # Stop auto-save
        await auto_save_manager.stop_auto_save()

        # Verify file was saved
        assert session_store.current_session_file.exists()
        assert not auto_save_manager.has_unsaved_changes

    async def test_set_state_provider(self, session_store):
        """Test setting state provider after initialization."""
        auto_save_manager = AutoSaveManager(session_store=session_store)

        sample_state = EngagementState(
            id="test",
            name="Test",
            session_metadata=SessionMetadata(session_id="test"),
        )

        def state_provider():
            return sample_state

        auto_save_manager.set_state_provider(state_provider)

        auto_save_manager.mark_changes()
        success = await auto_save_manager.force_save()
        assert success

    async def test_auto_save_with_exception(self, session_store):
        """Test auto-save behavior when state provider raises exception."""

        def failing_state_provider():
            raise Exception("Provider failed")

        auto_save_manager = AutoSaveManager(
            session_store=session_store,
            save_interval=1,
            state_provider=failing_state_provider,
        )

        auto_save_manager.mark_changes()
        success = await auto_save_manager.force_save()
        assert not success
        assert auto_save_manager.has_unsaved_changes  # Changes should remain marked

    async def test_stop_with_pending_changes(self, auto_save_manager, session_store):
        """Test stopping auto-save with pending changes triggers final save."""
        await auto_save_manager.start_auto_save()
        auto_save_manager.mark_changes()

        await auto_save_manager.stop_auto_save()

        # Final save should have been triggered
        assert session_store.current_session_file.exists()
        assert not auto_save_manager.has_unsaved_changes

    async def test_double_start_protection(self, auto_save_manager):
        """Test that starting auto-save twice doesn't create multiple tasks."""
        await auto_save_manager.start_auto_save()
        assert auto_save_manager.is_running

        # Try to start again
        await auto_save_manager.start_auto_save()
        assert auto_save_manager.is_running

        await auto_save_manager.stop_auto_save()

    async def test_last_save_time_tracking(self, auto_save_manager):
        """Test that last save time is tracked correctly."""
        import time

        old_time = auto_save_manager.last_save_time
        time.sleep(0.01)  # Small delay to ensure time difference

        await auto_save_manager.force_save()
        new_time = auto_save_manager.last_save_time

        assert new_time > old_time
