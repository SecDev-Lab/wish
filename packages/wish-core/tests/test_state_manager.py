"""Tests for state management functionality."""

from datetime import UTC

import pytest
from wish_models import CollectedData, Finding, Host, Target

from wish_core.events import DataCollected, EventBus, FindingAdded, HostDiscovered, ModeChanged
from wish_core.state.manager import InMemoryStateManager


@pytest.mark.unit
class TestInMemoryStateManager:
    """Test InMemoryStateManager implementation."""

    @pytest.fixture
    def event_bus(self):
        """Create an EventBus instance for testing."""
        return EventBus()

    @pytest.fixture
    def state_manager(self, event_bus):
        """Create a StateManager instance for testing."""
        return InMemoryStateManager(event_bus=event_bus)

    async def test_get_current_state(self, state_manager):
        """Test getting current state."""
        state = await state_manager.get_current_state()
        assert state.id == "default"
        assert state.name == "Default Engagement"
        assert state.session_metadata.session_id == "default"

    async def test_update_hosts_new_host(self, state_manager, event_bus):
        """Test adding a new host."""
        events = []

        async def handler(event):
            events.append(event)

        event_bus.subscribe(HostDiscovered, handler)

        host = Host(
            id="192.168.1.1",
            ip_address="192.168.1.1",
            hostnames=["test-host"],
            os_info="Linux",
            services=[],
            discovered_by="test",
        )

        await state_manager.update_hosts([host])

        state = await state_manager.get_current_state()
        assert "192.168.1.1" in state.hosts
        assert state.hosts["192.168.1.1"].ip_address == "192.168.1.1"

        # Check event was published
        assert len(events) == 1
        assert isinstance(events[0], HostDiscovered)
        assert events[0].host.ip_address == "192.168.1.1"

    async def test_update_hosts_existing_host(self, state_manager, event_bus):
        """Test updating an existing host."""
        events = []

        async def handler(event):
            events.append(event)

        event_bus.subscribe(HostDiscovered, handler)

        # Add initial host
        host1 = Host(
            id="192.168.1.1",
            ip_address="192.168.1.1",
            hostnames=["test-host"],
            os_info="Linux",
            services=[],
            discovered_by="test",
        )
        await state_manager.update_hosts([host1])

        # Update the same host
        from datetime import datetime

        from wish_models import Service

        host2 = Host(
            id="192.168.1.1",
            ip_address="192.168.1.1",
            hostnames=["test-host-updated"],
            os_info="Linux",
            services=[
                Service(
                    host_id="192.168.1.1",
                    port=80,
                    protocol="tcp",
                    service_name="http",
                    version="Apache 2.4",
                    state="open",
                    discovered_by="test",
                )
            ],
            discovered_by="test",
            discovered_at=datetime.now(UTC),
        )
        await state_manager.update_hosts([host2])

        state = await state_manager.get_current_state()
        host = state.hosts["192.168.1.1"]
        assert host.last_seen == host2.discovered_at
        assert len(host.services) == 1
        assert host.services[0].port == 80

        # Check events were published for both operations
        assert len(events) == 2

    async def test_update_hosts_deduplication(self, state_manager, event_bus):
        """Test that hosts with the same IP address are deduplicated."""
        from wish_models import Service

        # First scan - add host with 2 services
        host1 = Host(
            ip_address="10.10.10.3",
            hostnames=["lame.htb"],
            status="up",
            os_info="Linux 2.6",
            os_confidence=0.9,
            services=[
                Service(
                    host_id="dummy",
                    port=21,
                    protocol="tcp",
                    service_name="ftp",
                    product="vsftpd",
                    version="2.3.4",
                    state="open",
                    discovered_by="nmap",
                ),
                Service(
                    host_id="dummy",
                    port=22,
                    protocol="tcp",
                    service_name="ssh",
                    product="OpenSSH",
                    version="4.7p1",
                    state="open",
                    discovered_by="nmap",
                ),
            ],
            discovered_by="nmap",
        )

        await state_manager.update_hosts([host1])

        # Verify first host is added
        state = await state_manager.get_current_state()
        assert len(state.hosts) == 1
        first_host = list(state.hosts.values())[0]
        assert first_host.ip_address == "10.10.10.3"
        assert len(first_host.services) == 2

        # Second scan - same IP but different host ID, with overlapping and new services
        host2 = Host(
            ip_address="10.10.10.3",  # Same IP
            hostnames=["lame2.htb"],  # Different hostname
            status="up",
            os_info="Linux 2.6",
            os_confidence=0.95,  # Higher confidence
            mac_address="00:11:22:33:44:55",  # New MAC address
            services=[
                Service(
                    host_id="different",
                    port=22,  # Duplicate service
                    protocol="tcp",
                    service_name="ssh",
                    product="OpenSSH",
                    version="4.7p1",
                    state="open",
                    discovered_by="nmap",
                ),
                Service(
                    host_id="different",
                    port=139,  # New service
                    protocol="tcp",
                    service_name="netbios-ssn",
                    product="Samba",
                    version="3.0.20",
                    state="open",
                    discovered_by="nmap",
                ),
                Service(
                    host_id="different",
                    port=445,  # New service
                    protocol="tcp",
                    service_name="netbios-ssn",
                    product="Samba",
                    version="3.0.20",
                    state="open",
                    discovered_by="nmap",
                ),
            ],
            discovered_by="nmap",
        )

        await state_manager.update_hosts([host2])

        # Verify still only one host
        state = await state_manager.get_current_state()
        assert len(state.hosts) == 1, f"Expected 1 host, got {len(state.hosts)}"

        # Verify host was properly merged
        merged_host = list(state.hosts.values())[0]
        assert merged_host.ip_address == "10.10.10.3"
        assert len(merged_host.services) == 4, f"Expected 4 services, got {len(merged_host.services)}"
        assert "lame.htb" in merged_host.hostnames
        assert "lame2.htb" in merged_host.hostnames
        assert merged_host.os_confidence == 0.95  # Updated to higher confidence
        assert merged_host.mac_address == "00:11:22:33:44:55"  # MAC was added

        # Verify services are correct
        service_ports = {s.port for s in merged_host.services}
        assert service_ports == {21, 22, 139, 445}

    async def test_add_finding(self, state_manager, event_bus):
        """Test adding a finding."""
        events = []

        async def handler(event):
            events.append(event)

        event_bus.subscribe(FindingAdded, handler)

        finding = Finding(
            id="finding-1",
            title="SQL Injection",
            description="SQL injection vulnerability found",
            category="vulnerability",
            severity="high",
            target_type="host",
            host_id="192.168.1.1",
            discovered_by="test",
        )

        await state_manager.add_finding(finding)

        state = await state_manager.get_current_state()
        assert "finding-1" in state.findings
        assert state.findings["finding-1"].title == "SQL Injection"
        assert state.session_metadata.total_findings == 1

        # Check event was published
        assert len(events) == 1
        assert isinstance(events[0], FindingAdded)
        assert events[0].finding.id == "finding-1"

    async def test_add_collected_data(self, state_manager, event_bus):
        """Test adding collected data."""
        events = []

        async def handler(event):
            events.append(event)

        event_bus.subscribe(DataCollected, handler)

        data = CollectedData(
            id="data-1",
            type="file",
            content="base64-encoded-image",
            discovered_by="test",
        )

        await state_manager.add_collected_data(data)

        state = await state_manager.get_current_state()
        assert "data-1" in state.collected_data
        assert state.collected_data["data-1"].type == "file"

        # Check event was published
        assert len(events) == 1
        assert isinstance(events[0], DataCollected)
        assert events[0].data.id == "data-1"

    async def test_set_mode(self, state_manager, event_bus):
        """Test changing engagement mode."""
        events = []

        async def handler(event):
            events.append(event)

        event_bus.subscribe(ModeChanged, handler)

        await state_manager.set_mode("exploit")

        state = await state_manager.get_current_state()
        assert state.session_metadata.current_mode == "exploit"

        # Check event was published
        assert len(events) == 1
        assert isinstance(events[0], ModeChanged)
        assert events[0].old_mode == "recon"
        assert events[0].new_mode == "exploit"

    async def test_add_target(self, state_manager):
        """Test adding a target."""
        target = Target(
            id="target-1",
            scope="192.168.1.0/24",
            scope_type="cidr",
            name="Test Target",
            description="Target for testing",
        )

        await state_manager.add_target(target)

        state = await state_manager.get_current_state()
        assert "target-1" in state.targets
        assert state.targets["target-1"].name == "Test Target"

    async def test_remove_target(self, state_manager):
        """Test removing a target."""
        target = Target(
            id="target-1",
            scope="192.168.1.0/24",
            scope_type="cidr",
            name="Test Target",
            description="Target for testing",
        )

        await state_manager.add_target(target)

        state = await state_manager.get_current_state()
        assert "target-1" in state.targets

        await state_manager.remove_target("192.168.1.0/24")

        state = await state_manager.get_current_state()
        assert "target-1" not in state.targets

    async def test_remove_target_not_found(self, state_manager):
        """Test removing a non-existent target."""
        with pytest.raises(ValueError, match="Target '192.168.1.0/24' not found in scope"):
            await state_manager.remove_target("192.168.1.0/24")

    async def test_event_bus_property(self, state_manager, event_bus):
        """Test event bus property access."""
        assert state_manager.event_bus is event_bus
