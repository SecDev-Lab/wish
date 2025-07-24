"""Core model tests for all data models."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from wish_models.data import CollectedData
from wish_models.engagement import Target
from wish_models.finding import Finding
from wish_models.host import Host, Service
from wish_models.session import SessionMetadata
from wish_models.validation import ValidationError


class TestTarget:
    """Test Target model."""

    def test_target_creation_valid(self):
        """Test valid target creation."""
        target = Target(scope="192.168.1.0/24", scope_type="cidr", name="Test Network", description="Test environment")

        assert target.scope == "192.168.1.0/24"
        assert target.scope_type == "cidr"
        assert target.name == "Test Network"
        assert target.in_scope is True
        assert target.id is not None

    def test_target_ip_validation(self):
        """Test IP address validation."""
        target = Target(scope="192.168.1.1", scope_type="ip")
        assert target.scope == "192.168.1.1"

    def test_target_invalid_ip(self):
        """Test invalid IP address raises validation error."""
        with pytest.raises(ValidationError):
            Target(scope="invalid-ip", scope_type="ip")

    def test_target_domain_validation(self):
        """Test domain validation."""
        target = Target(scope="example.com", scope_type="domain")
        assert target.scope == "example.com"

    def test_target_invalid_domain(self):
        """Test invalid domain raises validation error."""
        with pytest.raises(ValidationError):
            Target(scope="invalid..domain", scope_type="domain")

    def test_target_url_validation(self):
        """Test URL validation."""
        target = Target(scope="https://example.com/app", scope_type="url")
        assert target.scope == "https://example.com/app"

    def test_target_cidr_validation(self):
        """Test CIDR validation."""
        target = Target(scope="10.0.0.0/8", scope_type="cidr")
        assert target.scope == "10.0.0.0/8"

    def test_target_future_date_validation(self):
        """Test that future dates are rejected."""
        future_date = datetime.now(UTC) + timedelta(days=1)
        with pytest.raises(ValidationError):
            Target(scope="192.168.1.1", scope_type="ip", added_at=future_date)


class TestHost:
    """Test Host model."""

    def test_host_creation_valid(self):
        """Test valid host creation."""
        host = Host(ip_address="192.168.1.100", discovered_by="nmap", status="up")

        assert host.ip_address == "192.168.1.100"
        assert host.status == "up"
        assert host.discovered_by == "nmap"
        assert len(host.services) == 0
        assert len(host.hostnames) == 0

    def test_host_invalid_ip(self):
        """Test invalid IP address raises validation error."""
        with pytest.raises(ValidationError):
            Host(ip_address="invalid-ip", discovered_by="nmap")

    def test_host_mac_address_validation(self):
        """Test MAC address validation."""
        host = Host(ip_address="192.168.1.100", mac_address="00:11:22:33:44:55", discovered_by="nmap")
        assert host.mac_address == "00:11:22:33:44:55"

    def test_host_invalid_mac_address(self):
        """Test invalid MAC address raises validation error."""
        with pytest.raises(ValidationError):
            Host(ip_address="192.168.1.100", mac_address="invalid-mac", discovered_by="nmap")

    def test_host_add_hostname(self):
        """Test adding hostname."""
        host = Host(ip_address="192.168.1.100", discovered_by="nmap")
        host.add_hostname("server.example.com")
        host.add_hostname("web.example.com")

        assert len(host.hostnames) == 2
        assert "server.example.com" in host.hostnames
        assert "web.example.com" in host.hostnames

    def test_host_add_duplicate_hostname(self):
        """Test adding duplicate hostname is prevented."""
        host = Host(ip_address="192.168.1.100", discovered_by="nmap")
        host.add_hostname("server.example.com")
        host.add_hostname("server.example.com")  # Duplicate

        assert len(host.hostnames) == 1

    def test_host_add_tag(self):
        """Test adding tag."""
        host = Host(ip_address="192.168.1.100", discovered_by="nmap")
        host.add_tag("DMZ")
        host.add_tag("web-server")

        assert len(host.tags) == 2
        assert "DMZ" in host.tags

    def test_host_os_confidence_validation(self):
        """Test OS confidence score validation."""
        host = Host(ip_address="192.168.1.100", os_confidence=0.85, discovered_by="nmap")
        assert host.os_confidence == 0.85

    def test_host_invalid_os_confidence(self):
        """Test invalid OS confidence score raises validation error."""
        with pytest.raises(ValidationError):
            Host(
                ip_address="192.168.1.100",
                os_confidence=1.5,  # Invalid: > 1.0
                discovered_by="nmap",
            )


class TestService:
    """Test Service model."""

    def test_service_creation_valid(self):
        """Test valid service creation."""
        service = Service(
            host_id=str(uuid4()), port=80, protocol="tcp", service_name="http", state="open", discovered_by="nmap"
        )

        assert service.port == 80
        assert service.protocol == "tcp"
        assert service.service_name == "http"

    def test_service_port_validation(self):
        """Test port number validation."""
        service = Service(host_id=str(uuid4()), port=443, protocol="tcp", state="open", discovered_by="nmap")
        assert service.port == 443

    def test_service_invalid_port_low(self):
        """Test invalid port number (too low) raises validation error."""
        with pytest.raises(ValidationError):
            Service(
                host_id=str(uuid4()),
                port=0,  # Invalid: < 1
                protocol="tcp",
                state="open",
                discovered_by="nmap",
            )

    def test_service_invalid_port_high(self):
        """Test invalid port number (too high) raises validation error."""
        with pytest.raises(ValidationError):
            Service(
                host_id=str(uuid4()),
                port=65536,  # Invalid: > 65535
                protocol="tcp",
                state="open",
                discovered_by="nmap",
            )

    def test_service_confidence_validation(self):
        """Test confidence score validation."""
        service = Service(
            host_id=str(uuid4()), port=80, protocol="tcp", state="open", confidence=0.9, discovered_by="nmap"
        )
        assert service.confidence == 0.9

    def test_service_invalid_confidence(self):
        """Test invalid confidence score raises validation error."""
        with pytest.raises(ValidationError):
            Service(
                host_id=str(uuid4()),
                port=80,
                protocol="tcp",
                state="open",
                confidence=2.0,  # Invalid: > 1.0
                discovered_by="nmap",
            )


class TestFinding:
    """Test Finding model."""

    def test_finding_creation_valid(self):
        """Test valid finding creation."""
        finding = Finding(
            title="SQL Injection",
            description="SQL injection vulnerability found",
            category="vulnerability",
            severity="high",
            target_type="application",
            discovered_by="sqlmap",
        )

        assert finding.title == "SQL Injection"
        assert finding.severity == "high"
        assert finding.category == "vulnerability"
        assert finding.status == "new"

    def test_finding_add_cve(self):
        """Test adding CVE ID."""
        finding = Finding(
            title="Test Finding",
            description="Test",
            category="vulnerability",
            target_type="host",
            discovered_by="manual",
        )

        finding.add_cve("CVE-2021-1234")
        finding.add_cve("CVE-2021-5678")

        assert len(finding.cve_ids) == 2
        assert "CVE-2021-1234" in finding.cve_ids

    def test_finding_invalid_cve_format(self):
        """Test invalid CVE format raises validation error."""
        finding = Finding(
            title="Test Finding",
            description="Test",
            category="vulnerability",
            target_type="host",
            discovered_by="manual",
        )

        with pytest.raises(ValidationError):
            finding.add_cve("invalid-cve")

    def test_finding_mark_verified(self):
        """Test marking finding as verified."""
        finding = Finding(
            title="Test Finding",
            description="Test",
            category="vulnerability",
            target_type="host",
            discovered_by="manual",
        )

        finding.mark_verified()
        assert finding.status == "confirmed"

    def test_finding_mark_false_positive(self):
        """Test marking finding as false positive."""
        finding = Finding(
            title="Test Finding",
            description="Test",
            category="vulnerability",
            target_type="host",
            discovered_by="manual",
        )

        finding.mark_false_positive()
        assert finding.status == "false_positive"

    def test_finding_is_critical(self):
        """Test critical finding detection."""
        finding_critical = Finding(
            title="Critical Issue",
            description="Test",
            category="vulnerability",
            severity="critical",
            target_type="host",
            discovered_by="manual",
        )

        finding_low = Finding(
            title="Low Issue",
            description="Test",
            category="misconfiguration",
            severity="low",
            target_type="host",
            discovered_by="manual",
        )

        assert finding_critical.is_critical() is True
        assert finding_low.is_critical() is False

    def test_finding_url_validation(self):
        """Test URL validation."""
        finding = Finding(
            title="Web Issue",
            description="Test",
            category="vulnerability",
            target_type="application",
            url="https://example.com/vulnerable",
            discovered_by="manual",
        )

        assert finding.url == "https://example.com/vulnerable"

    def test_finding_invalid_url(self):
        """Test invalid URL raises validation error."""
        with pytest.raises(ValidationError):
            Finding(
                title="Web Issue",
                description="Test",
                category="vulnerability",
                target_type="application",
                url="invalid-url",
                discovered_by="manual",
            )


class TestCollectedData:
    """Test CollectedData model."""

    def test_collected_data_creation_valid(self):
        """Test valid collected data creation."""
        data = CollectedData(type="credentials", content="password123", username="admin", discovered_by="manual")

        assert data.type == "credentials"
        assert data.content == "password123"
        assert data.username == "admin"
        assert data.is_sensitive is True
        assert data.working is False

    def test_collected_data_mark_working(self):
        """Test marking credentials as working."""
        data = CollectedData(type="credentials", content="password123", username="admin", discovered_by="manual")

        data.mark_as_working()
        assert data.working is True
        assert data.analyzed is True

    def test_collected_data_is_credential(self):
        """Test credential type detection."""
        cred_data = CollectedData(type="credentials", content="password123", discovered_by="manual")

        file_data = CollectedData(type="file", content="file content", discovered_by="manual")

        assert cred_data.is_credential() is True
        assert file_data.is_credential() is False

    def test_collected_data_credential_summary(self):
        """Test credential summary generation."""
        data = CollectedData(
            type="credentials", content="password123", username="admin", domain="example.com", discovered_by="manual"
        )

        summary = data.get_credential_summary()
        assert summary == "admin@example.com"

    def test_collected_data_link_finding(self):
        """Test linking to source finding."""
        data = CollectedData(type="credentials", content="password123", discovered_by="manual")

        finding_id = str(uuid4())
        data.link_source_finding(finding_id)

        assert data.source_finding_id == finding_id


class TestSessionMetadata:
    """Test SessionMetadata model."""

    def test_session_metadata_creation(self):
        """Test session metadata creation."""
        session = SessionMetadata(engagement_name="Test Engagement")

        assert session.engagement_name == "Test Engagement"
        assert session.current_mode == "recon"
        assert session.total_commands == 0

    def test_session_add_command(self):
        """Test adding command to history."""
        session = SessionMetadata()

        session.add_command("nmap -sV 192.168.1.1")
        session.add_command("dirb https://example.com")

        assert session.total_commands == 2
        assert len(session.command_history) == 2
        assert "nmap -sV 192.168.1.1" in session.command_history

    def test_session_command_history_limit(self):
        """Test command history is limited to 100 entries."""
        session = SessionMetadata()

        # Add 150 commands
        for i in range(150):
            session.add_command(f"command_{i}")

        assert len(session.command_history) == 100
        assert session.total_commands == 150
        # Should keep latest commands
        assert "command_149" in session.command_history
        assert "command_0" not in session.command_history

    def test_session_change_mode(self):
        """Test mode change."""
        session = SessionMetadata()
        original_mode = session.current_mode

        session.change_mode("exploit")

        assert session.current_mode == "exploit"
        assert len(session.mode_history) == 1
        assert session.mode_history[0][0] == original_mode

    def test_session_add_tag(self):
        """Test adding tag."""
        session = SessionMetadata()

        session.add_tag("external")
        session.add_tag("web-app")
        session.add_tag("external")  # Duplicate

        assert len(session.tags) == 2
        assert "external" in session.tags

    def test_session_duration(self):
        """Test session duration calculation."""
        session = SessionMetadata()

        # Simulate some time passing
        import time

        time.sleep(0.1)
        session.update_activity()

        duration = session.get_session_duration()
        assert duration > 0
