"""Tests for model relationships and integration."""

import pytest

from wish_models.data import CollectedData
from wish_models.engagement import EngagementState, Target
from wish_models.finding import Finding
from wish_models.host import Host, Service
from wish_models.session import SessionMetadata


class TestModelRelationships:
    """Test relationships between different models."""

    @pytest.fixture
    def engagement_setup(self):
        """Set up a complete engagement with interconnected data."""
        session = SessionMetadata(engagement_name="Relationship Test")
        engagement = EngagementState(name="Test Engagement", session_metadata=session)

        # Add target
        target = Target(scope="192.168.1.0/24", scope_type="cidr")
        engagement.add_target(target)

        # Add host
        host = Host(ip_address="192.168.1.100", status="up", discovered_by="nmap")
        engagement.hosts[host.id] = host

        # Add services to host
        web_service = Service(
            host_id=host.id, port=80, protocol="tcp", service_name="http", state="open", discovered_by="nmap"
        )
        ssh_service = Service(
            host_id=host.id, port=22, protocol="tcp", service_name="ssh", state="open", discovered_by="nmap"
        )

        host.add_service(web_service)
        host.add_service(ssh_service)

        return {
            "engagement": engagement,
            "target": target,
            "host": host,
            "web_service": web_service,
            "ssh_service": ssh_service,
        }

    def test_host_service_relationship(self, engagement_setup):
        """Test host-service relationships."""
        host = engagement_setup["host"]
        web_service = engagement_setup["web_service"]
        ssh_service = engagement_setup["ssh_service"]

        # Verify services are added to host
        assert len(host.services) == 2
        assert web_service in host.services
        assert ssh_service in host.services

        # Verify service host_id is set correctly
        assert web_service.host_id == host.id
        assert ssh_service.host_id == host.id

        # Test adding duplicate service (same port/protocol)
        duplicate_web = Service(
            host_id=host.id,
            port=80,
            protocol="tcp",
            state="open",
            service_name="apache",
            version="2.4",
            discovered_by="nmap",
        )

        host.add_service(duplicate_web)

        # Should still have 2 services, but updated info
        assert len(host.services) == 2
        # Find the web service and check it was updated
        web_svc = next(svc for svc in host.services if svc.port == 80)
        assert web_svc.service_name == "apache"  # Updated
        assert web_svc.version == "2.4"  # Updated

    def test_finding_host_service_relationship(self, engagement_setup):
        """Test finding relationships with hosts and services."""
        engagement = engagement_setup["engagement"]
        host = engagement_setup["host"]
        web_service = engagement_setup["web_service"]

        # Create finding related to the web service
        finding = Finding(
            title="Web Server Vulnerability",
            description="Found vulnerability in web server",
            category="vulnerability",
            severity="high",
            target_type="service",
            host_id=host.id,
            service_id=web_service.id,
            discovered_by="nikto",
        )

        engagement.findings[finding.id] = finding

        # Verify relationships
        assert finding.host_id == host.id
        assert finding.service_id == web_service.id

        # Test finding without specific service (host-level)
        host_finding = Finding(
            title="Host Misconfiguration",
            description="General host issue",
            category="misconfiguration",
            target_type="host",
            host_id=host.id,
            discovered_by="manual",
        )

        engagement.findings[host_finding.id] = host_finding

        assert host_finding.host_id == host.id
        assert host_finding.service_id is None

    def test_collected_data_relationships(self, engagement_setup):
        """Test collected data relationships with findings and sources."""
        engagement = engagement_setup["engagement"]
        host = engagement_setup["host"]
        ssh_service = engagement_setup["ssh_service"]

        # Create finding that leads to credential discovery
        finding = Finding(
            title="Weak SSH Password",
            description="Weak password found via brute force",
            category="weak_authentication",
            target_type="service",
            host_id=host.id,
            service_id=ssh_service.id,
            discovered_by="hydra",
        )
        engagement.findings[finding.id] = finding

        # Create collected data from this finding
        credentials = CollectedData(
            type="credentials",
            content="admin:password123",
            username="admin",
            source_host_id=host.id,
            source_service_id=ssh_service.id,
            source_finding_id=finding.id,
            discovered_by="hydra",
        )
        engagement.collected_data[credentials.id] = credentials

        # Link the relationships
        finding.link_collected_data(credentials.id)
        credentials.link_source_finding(finding.id)

        # Now create a new finding derived from using these credentials
        derived_finding = Finding(
            title="Privilege Escalation",
            description="Admin access leads to privilege escalation",
            category="vulnerability",
            target_type="host",
            host_id=host.id,
            discovered_by="manual",
        )
        engagement.findings[derived_finding.id] = derived_finding

        # Link the derived finding back to the credentials
        credentials.add_derived_finding(derived_finding.id)

        # Verify all relationships
        assert credentials.source_finding_id == finding.id
        assert credentials.source_host_id == host.id
        assert credentials.source_service_id == ssh_service.id
        assert credentials.id in finding.related_collected_data_ids
        assert derived_finding.id in credentials.derived_finding_ids

    def test_engagement_state_aggregations(self, engagement_setup):
        """Test engagement state aggregation methods with real data."""
        engagement = engagement_setup["engagement"]
        host = engagement_setup["host"]

        # Add more hosts with different states
        host2 = Host(ip_address="192.168.1.101", status="down", discovered_by="nmap")
        host3 = Host(ip_address="192.168.1.102", status="up", discovered_by="nmap")

        # Add closed service to host3
        closed_service = Service(host_id=host3.id, port=443, protocol="tcp", state="closed", discovered_by="nmap")
        host3.add_service(closed_service)

        engagement.hosts[host2.id] = host2
        engagement.hosts[host3.id] = host3

        # Add various findings
        critical_finding = Finding(
            title="Critical Issue",
            description="Critical vulnerability",
            category="vulnerability",
            severity="critical",
            target_type="host",
            host_id=host.id,
            discovered_by="manual",
        )

        low_finding = Finding(
            title="Minor Issue",
            description="Low severity issue",
            category="misconfiguration",
            severity="low",
            target_type="host",
            host_id=host3.id,
            discovered_by="manual",
        )

        engagement.findings[critical_finding.id] = critical_finding
        engagement.findings[low_finding.id] = low_finding

        # Add collected data
        sensitive_data = CollectedData(type="credentials", content="secret", is_sensitive=True, discovered_by="manual")

        working_creds = CollectedData(
            type="credentials", content="admin:valid", working=True, is_sensitive=False, discovered_by="manual"
        )

        other_data = CollectedData(type="file", content="config file", is_sensitive=False, discovered_by="manual")

        engagement.collected_data[sensitive_data.id] = sensitive_data
        engagement.collected_data[working_creds.id] = working_creds
        engagement.collected_data[other_data.id] = other_data

        # Test aggregations
        active_hosts = engagement.get_active_hosts()
        assert len(active_hosts) == 2  # host and host3 are up
        assert host in active_hosts
        assert host3 in active_hosts
        assert host2 not in active_hosts

        open_services = engagement.get_open_services()
        assert len(open_services) == 2  # web_service and ssh_service

        all_findings = engagement.get_all_findings()
        assert len(all_findings) == 2

        sensitive_items = engagement.get_sensitive_collected_data()
        assert len(sensitive_items) == 1
        assert sensitive_data in sensitive_items

        working_credentials = engagement.get_working_credentials()
        assert len(working_credentials) == 1
        assert working_creds in working_credentials

    def test_circular_relationships(self, engagement_setup):
        """Test handling of circular relationships between findings and collected data."""
        engagement = engagement_setup["engagement"]
        host = engagement_setup["host"]

        # Create initial finding
        finding1 = Finding(
            title="Initial Discovery",
            description="First finding",
            category="vulnerability",
            target_type="host",
            host_id=host.id,
            discovered_by="scanner",
        )
        engagement.findings[finding1.id] = finding1

        # Create data from finding1
        data1 = CollectedData(
            type="credentials", content="user:pass", source_finding_id=finding1.id, discovered_by="scanner"
        )
        engagement.collected_data[data1.id] = data1

        # Link finding1 -> data1
        finding1.link_collected_data(data1.id)

        # Create finding2 derived from data1
        finding2 = Finding(
            title="Derived Finding",
            description="Found using credentials",
            category="vulnerability",
            target_type="host",
            host_id=host.id,
            discovered_by="manual",
        )
        engagement.findings[finding2.id] = finding2

        # Link data1 -> finding2
        data1.add_derived_finding(finding2.id)

        # Create data2 from finding2
        data2 = CollectedData(
            type="file", content="sensitive file", source_finding_id=finding2.id, discovered_by="manual"
        )
        engagement.collected_data[data2.id] = data2

        # Link finding2 -> data2
        finding2.link_collected_data(data2.id)

        # Verify the chain: finding1 -> data1 -> finding2 -> data2
        assert data1.id in finding1.related_collected_data_ids
        assert finding2.id in data1.derived_finding_ids
        assert data2.id in finding2.related_collected_data_ids
        assert data1.source_finding_id == finding1.id
        assert data2.source_finding_id == finding2.id

    def test_host_service_consistency(self, engagement_setup):
        """Test consistency between host and service data."""
        engagement = engagement_setup["engagement"]
        host = engagement_setup["host"]

        # Get all services from all hosts
        all_services = engagement.get_open_services()

        # Verify each service's host_id points to an existing host
        for service in all_services:
            assert service.host_id in engagement.hosts
            host_with_service = engagement.hosts[service.host_id]
            assert service in host_with_service.services

        # Verify host.services contains services with correct host_id
        for service in host.services:
            assert service.host_id == host.id

        # Test getting open ports from host
        open_ports = host.get_open_ports()
        expected_ports = [svc.port for svc in host.services if svc.state == "open"]
        assert set(open_ports) == set(expected_ports)
