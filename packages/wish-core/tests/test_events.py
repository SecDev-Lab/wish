"""Tests for event system functionality."""

import pytest
from wish_models import CollectedData, Finding, Host

from wish_core.events import DataCollected, EventBus, FindingAdded, HostDiscovered, ModeChanged


@pytest.mark.unit
class TestEventBus:
    """Test EventBus functionality."""

    @pytest.fixture
    def event_bus(self):
        """Create an EventBus instance for testing."""
        return EventBus()

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

    async def test_subscribe_and_publish_host_discovered(self, event_bus, sample_host):
        """Test subscribing to and publishing HostDiscovered events."""
        received_events = []

        async def handler(event):
            received_events.append(event)

        event_bus.subscribe(HostDiscovered, handler)

        event = HostDiscovered(host=sample_host)
        await event_bus.publish(event)

        assert len(received_events) == 1
        assert isinstance(received_events[0], HostDiscovered)
        assert received_events[0].host.ip_address == "192.168.1.1"

    async def test_subscribe_and_publish_finding_added(self, event_bus, sample_finding):
        """Test subscribing to and publishing FindingAdded events."""
        received_events = []

        async def handler(event):
            received_events.append(event)

        event_bus.subscribe(FindingAdded, handler)

        event = FindingAdded(finding=sample_finding)
        await event_bus.publish(event)

        assert len(received_events) == 1
        assert isinstance(received_events[0], FindingAdded)
        assert received_events[0].finding.title == "Test Finding"

    async def test_subscribe_and_publish_data_collected(self, event_bus, sample_collected_data):
        """Test subscribing to and publishing DataCollected events."""
        received_events = []

        async def handler(event):
            received_events.append(event)

        event_bus.subscribe(DataCollected, handler)

        event = DataCollected(data=sample_collected_data)
        await event_bus.publish(event)

        assert len(received_events) == 1
        assert isinstance(received_events[0], DataCollected)
        assert received_events[0].data.type == "file"

    async def test_subscribe_and_publish_mode_changed(self, event_bus):
        """Test subscribing to and publishing ModeChanged events."""
        received_events = []

        async def handler(event):
            received_events.append(event)

        event_bus.subscribe(ModeChanged, handler)

        event = ModeChanged(old_mode="recon", new_mode="exploit")
        await event_bus.publish(event)

        assert len(received_events) == 1
        assert isinstance(received_events[0], ModeChanged)
        assert received_events[0].old_mode == "recon"
        assert received_events[0].new_mode == "exploit"

    async def test_multiple_handlers_same_event(self, event_bus, sample_host):
        """Test multiple handlers for the same event type."""
        received_events_1 = []
        received_events_2 = []

        async def handler1(event):
            received_events_1.append(event)

        async def handler2(event):
            received_events_2.append(event)

        event_bus.subscribe(HostDiscovered, handler1)
        event_bus.subscribe(HostDiscovered, handler2)

        event = HostDiscovered(host=sample_host)
        await event_bus.publish(event)

        assert len(received_events_1) == 1
        assert len(received_events_2) == 1
        assert received_events_1[0] is event
        assert received_events_2[0] is event

    async def test_publish_without_subscribers(self, event_bus, sample_host):
        """Test publishing events without any subscribers."""
        # Should not raise any errors
        event = HostDiscovered(host=sample_host)
        await event_bus.publish(event)

    async def test_multiple_event_types(self, event_bus, sample_host, sample_finding):
        """Test handling multiple different event types."""
        host_events = []
        finding_events = []

        async def host_handler(event):
            host_events.append(event)

        async def finding_handler(event):
            finding_events.append(event)

        event_bus.subscribe(HostDiscovered, host_handler)
        event_bus.subscribe(FindingAdded, finding_handler)

        # Publish different events
        await event_bus.publish(HostDiscovered(host=sample_host))
        await event_bus.publish(FindingAdded(finding=sample_finding))

        assert len(host_events) == 1
        assert len(finding_events) == 1
        assert isinstance(host_events[0], HostDiscovered)
        assert isinstance(finding_events[0], FindingAdded)

    async def test_event_handler_exceptions(self, event_bus, sample_host):
        """Test that handler exceptions don't break the event system."""
        successful_events = []

        async def failing_handler(event):
            raise Exception("Handler failed")

        async def successful_handler(event):
            successful_events.append(event)

        event_bus.subscribe(HostDiscovered, failing_handler)
        event_bus.subscribe(HostDiscovered, successful_handler)

        # This should not raise an exception despite the failing handler
        event = HostDiscovered(host=sample_host)
        try:
            await event_bus.publish(event)
        except Exception:
            pytest.fail("Event publishing should handle handler exceptions gracefully")

        # The successful handler should still have received the event
        assert len(successful_events) == 1
