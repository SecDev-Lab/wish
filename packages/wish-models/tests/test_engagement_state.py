"""Tests for EngagementState model and its functionality."""

import pytest

from wish_models.data import CollectedData
from wish_models.engagement import EngagementState, Target
from wish_models.finding import Finding
from wish_models.host import Host, Service
from wish_models.session import SessionMetadata


class TestEngagementState:
    """Test EngagementState model."""

    @pytest.fixture
    def sample_session_metadata(self):
        """Create sample session metadata."""
        return SessionMetadata(engagement_name="Test Engagement")

    @pytest.fixture
    def sample_engagement_state(self, sample_session_metadata):
        """Create sample engagement state."""
        return EngagementState(name="Test Penetration Test", session_metadata=sample_session_metadata)

    def test_engagement_state_creation(self, sample_session_metadata):
        """Test engagement state creation."""
        state = EngagementState(name="Test Engagement", session_metadata=sample_session_metadata)

        assert state.name == "Test Engagement"
        assert len(state.targets) == 0
        assert len(state.hosts) == 0
        assert len(state.findings) == 0
        assert len(state.collected_data) == 0

    def test_add_target(self, sample_engagement_state):
        """Test adding target to engagement."""
        target = Target(scope="192.168.1.0/24", scope_type="cidr", name="Test Network")

        sample_engagement_state.add_target(target)

        assert len(sample_engagement_state.targets) == 1
        assert target.id in sample_engagement_state.targets

    def test_get_active_hosts(self, sample_engagement_state):
        """Test getting active hosts."""
        # Add some hosts
        host1 = Host(ip_address="192.168.1.100", status="up", discovered_by="nmap")
        host2 = Host(ip_address="192.168.1.101", status="down", discovered_by="nmap")
        host3 = Host(ip_address="192.168.1.102", status="up", discovered_by="nmap")

        sample_engagement_state.hosts[host1.id] = host1
        sample_engagement_state.hosts[host2.id] = host2
        sample_engagement_state.hosts[host3.id] = host3

        active_hosts = sample_engagement_state.get_active_hosts()

        assert len(active_hosts) == 2
        assert host1 in active_hosts
        assert host3 in active_hosts
        assert host2 not in active_hosts

    def test_get_open_services(self, sample_engagement_state):
        """Test getting open services."""
        host = Host(ip_address="192.168.1.100", discovered_by="nmap")

        service1 = Service(host_id=host.id, port=80, protocol="tcp", state="open", discovered_by="nmap")
        service2 = Service(host_id=host.id, port=443, protocol="tcp", state="closed", discovered_by="nmap")
        service3 = Service(host_id=host.id, port=22, protocol="tcp", state="open", discovered_by="nmap")

        host.services = [service1, service2, service3]
        sample_engagement_state.hosts[host.id] = host

        open_services = sample_engagement_state.get_open_services()

        assert len(open_services) == 2
        assert service1 in open_services
        assert service3 in open_services
        assert service2 not in open_services

    def test_get_all_findings(self, sample_engagement_state):
        """Test getting all findings."""
        finding1 = Finding(
            title="SQL Injection",
            description="Test",
            category="vulnerability",
            target_type="application",
            discovered_by="sqlmap",
        )
        finding2 = Finding(
            title="Weak Password",
            description="Test",
            category="weak_authentication",
            target_type="host",
            discovered_by="hydra",
        )

        sample_engagement_state.findings[finding1.id] = finding1
        sample_engagement_state.findings[finding2.id] = finding2

        all_findings = sample_engagement_state.get_all_findings()

        assert len(all_findings) == 2
        assert finding1 in all_findings
        assert finding2 in all_findings

    def test_get_sensitive_collected_data(self, sample_engagement_state):
        """Test getting sensitive collected data."""
        sensitive_data = CollectedData(
            type="credentials", content="password123", is_sensitive=True, discovered_by="manual"
        )

        public_data = CollectedData(type="file", content="public info", is_sensitive=False, discovered_by="manual")

        sample_engagement_state.collected_data[sensitive_data.id] = sensitive_data
        sample_engagement_state.collected_data[public_data.id] = public_data

        sensitive_items = sample_engagement_state.get_sensitive_collected_data()

        assert len(sensitive_items) == 1
        assert sensitive_data in sensitive_items
        assert public_data not in sensitive_items

    def test_get_working_credentials(self, sample_engagement_state):
        """Test getting working credentials."""
        working_cred = CollectedData(
            type="credentials", content="admin:password123", working=True, discovered_by="manual"
        )

        failed_cred = CollectedData(type="credentials", content="user:wrongpass", working=False, discovered_by="manual")

        other_data = CollectedData(
            type="file",
            content="some file",
            working=True,  # Not a credential
            discovered_by="manual",
        )

        sample_engagement_state.collected_data[working_cred.id] = working_cred
        sample_engagement_state.collected_data[failed_cred.id] = failed_cred
        sample_engagement_state.collected_data[other_data.id] = other_data

        working_creds = sample_engagement_state.get_working_credentials()

        assert len(working_creds) == 1
        assert working_cred in working_creds
        assert failed_cred not in working_creds
        assert other_data not in working_creds

    def test_change_mode(self, sample_engagement_state):
        """Test changing engagement mode."""
        original_mode = sample_engagement_state.get_current_mode()

        sample_engagement_state.change_mode("exploit")

        assert sample_engagement_state.get_current_mode() == "exploit"
        assert len(sample_engagement_state.session_metadata.mode_history) == 1
        assert sample_engagement_state.session_metadata.mode_history[0][0] == original_mode

    def test_add_command_to_history(self, sample_engagement_state):
        """Test adding command to history."""
        command = "nmap -sV 192.168.1.100"

        sample_engagement_state.add_command_to_history(command)

        assert sample_engagement_state.session_metadata.total_commands == 1
        assert command in sample_engagement_state.session_metadata.command_history

    def test_update_timestamp(self, sample_engagement_state):
        """Test timestamp updates."""
        original_time = sample_engagement_state.updated_at
        original_activity = sample_engagement_state.session_metadata.last_activity

        # Wait a small amount to ensure timestamp difference
        import time

        time.sleep(0.01)

        sample_engagement_state.update_timestamp()

        assert sample_engagement_state.updated_at > original_time
        assert sample_engagement_state.session_metadata.last_activity > original_activity

    def test_engagement_state_with_complex_data(self, sample_session_metadata):
        """Test engagement state with complex interconnected data."""
        state = EngagementState(name="Complex Test", session_metadata=sample_session_metadata)

        # Add target
        target = Target(scope="192.168.1.0/24", scope_type="cidr")
        state.add_target(target)

        # Add host
        host = Host(ip_address="192.168.1.100", status="up", discovered_by="nmap")
        service = Service(host_id=host.id, port=80, protocol="tcp", state="open", discovered_by="nmap")
        host.services.append(service)
        state.hosts[host.id] = host

        # Add finding related to the service
        finding = Finding(
            title="Web Vulnerability",
            description="Found on web service",
            category="vulnerability",
            target_type="service",
            host_id=host.id,
            service_id=service.id,
            discovered_by="nikto",
        )
        state.findings[finding.id] = finding

        # Add collected data from the finding
        data = CollectedData(
            type="credentials",
            content="admin:password",
            source_host_id=host.id,
            source_service_id=service.id,
            source_finding_id=finding.id,
            discovered_by="manual",
        )
        finding.link_collected_data(data.id)
        data.add_derived_finding(finding.id)
        state.collected_data[data.id] = data

        # Verify relationships
        assert len(state.get_active_hosts()) == 1
        assert len(state.get_open_services()) == 1
        assert len(state.get_all_findings()) == 1
        assert len(state.get_sensitive_collected_data()) == 1

        # Verify data relationships
        assert data.source_finding_id == finding.id
        assert data.source_host_id == host.id
        assert data.source_service_id == service.id
        assert finding.id in data.derived_finding_ids
        assert data.id in finding.related_collected_data_ids
