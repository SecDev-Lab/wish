"""Tests for state change tracker functionality."""

import tempfile
from unittest.mock import Mock

import pytest
from wish_models import CollectedData, Finding, Host

from wish_core.persistence.auto_save import AutoSaveManager
from wish_core.persistence.session_store import SessionStore
from wish_core.persistence.state_tracker import StateChangeTracker


@pytest.mark.unit
class TestStateChangeTracker:
    """Test StateChangeTracker functionality."""

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
    def auto_save_manager(self, session_store):
        """Create an AutoSaveManager instance for testing."""
        return AutoSaveManager(session_store=session_store)

    @pytest.fixture
    def state_tracker(self, auto_save_manager):
        """Create a StateChangeTracker instance for testing."""
        return StateChangeTracker(auto_save_manager=auto_save_manager)

    @pytest.fixture
    def sample_host(self):
        """Create a sample Host for testing."""
        return Host(
            id="192.168.1.1",
            ip_address="192.168.1.1",
            hostnames=["test-host"],
            os_info="Linux",
            services=[],
            discovered_by="test",
        )

    @pytest.fixture
    def sample_finding(self):
        """Create a sample Finding for testing."""
        return Finding(
            id="finding-1",
            title="Test Finding",
            description="A test finding",
            category="vulnerability",
            severity="medium",
            target_type="host",
            host_id="192.168.1.1",
            discovered_by="test",
        )

    @pytest.fixture
    def sample_collected_data(self):
        """Create a sample CollectedData for testing."""
        return CollectedData(
            id="data-1",
            type="file",
            content="Test log content",
            discovered_by="test",
        )

    def test_track_host_change(self, state_tracker, auto_save_manager, sample_host):
        """Test tracking host changes."""
        # Mock the auto_save_manager
        auto_save_manager.mark_changes = Mock()

        state_tracker.track_host_change(sample_host, "added")

        auto_save_manager.mark_changes.assert_called_once()

    def test_track_finding_change(self, state_tracker, auto_save_manager, sample_finding):
        """Test tracking finding changes."""
        auto_save_manager.mark_changes = Mock()

        state_tracker.track_finding_change(sample_finding, "added")

        auto_save_manager.mark_changes.assert_called_once()

    def test_track_data_collection(self, state_tracker, auto_save_manager, sample_collected_data):
        """Test tracking data collection changes."""
        auto_save_manager.mark_changes = Mock()

        state_tracker.track_data_collection(sample_collected_data, "added")

        auto_save_manager.mark_changes.assert_called_once()

    def test_track_mode_change(self, state_tracker, auto_save_manager):
        """Test tracking mode changes."""
        auto_save_manager.mark_changes = Mock()

        state_tracker.track_mode_change("recon", "exploit")

        auto_save_manager.mark_changes.assert_called_once()

    def test_track_command_execution(self, state_tracker, auto_save_manager):
        """Test tracking command execution."""
        auto_save_manager.mark_changes = Mock()

        state_tracker.track_command_execution("nmap -sS 192.168.1.1")

        auto_save_manager.mark_changes.assert_called_once()

    def test_track_target_change(self, state_tracker, auto_save_manager):
        """Test tracking target changes."""
        auto_save_manager.mark_changes = Mock()

        state_tracker.track_target_change("target-1", "added")

        auto_save_manager.mark_changes.assert_called_once()

    def test_track_session_change(self, state_tracker, auto_save_manager):
        """Test tracking general session changes."""
        auto_save_manager.mark_changes = Mock()

        state_tracker.track_session_change("metadata_update", "session name changed")

        auto_save_manager.mark_changes.assert_called_once()

    def test_multiple_changes_tracked(self, state_tracker, auto_save_manager, sample_host, sample_finding):
        """Test that multiple changes are all tracked."""
        auto_save_manager.mark_changes = Mock()

        # Trigger multiple changes
        state_tracker.track_host_change(sample_host, "added")
        state_tracker.track_finding_change(sample_finding, "added")
        state_tracker.track_command_execution("ls -la")

        # Should have been called once for each change
        assert auto_save_manager.mark_changes.call_count == 3

    def test_tracker_with_real_auto_save(self, session_store):
        """Test state tracker with real auto save manager."""
        from wish_models import EngagementState, SessionMetadata

        # Create real auto save manager with state provider
        sample_state = EngagementState(
            id="test",
            name="Test",
            session_metadata=SessionMetadata(session_id="test"),
        )

        auto_save_manager = AutoSaveManager(
            session_store=session_store,
            state_provider=lambda: sample_state,
        )
        state_tracker = StateChangeTracker(auto_save_manager)

        # Track a change
        sample_host = Host(
            id="192.168.1.1",
            ip_address="192.168.1.1",
            hostnames=["test-host"],
            os_info="Linux",
            services=[],
            discovered_by="test",
        )

        state_tracker.track_host_change(sample_host, "added")

        # Verify changes were marked
        assert auto_save_manager.has_unsaved_changes
