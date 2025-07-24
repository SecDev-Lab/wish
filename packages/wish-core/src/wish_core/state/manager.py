"""State management implementation."""

from abc import ABC, abstractmethod

from wish_models import (
    CollectedData,
    EngagementState,
    Finding,
    Host,
    SessionMetadata,
    Target,
)

from ..events import DataCollected, EventBus, FindingAdded, HostDiscovered, ModeChanged


class StateManager(ABC):
    """Abstract base class for engagement state management."""

    @abstractmethod
    async def get_current_state(self) -> EngagementState:
        """Get the current engagement state."""
        pass

    @abstractmethod
    async def update_hosts(self, hosts: list[Host]) -> None:
        """Update host information with merge logic."""
        pass

    @abstractmethod
    async def add_finding(self, finding: Finding) -> None:
        """Add a finding to the engagement."""
        pass

    @abstractmethod
    async def add_collected_data(self, data: CollectedData) -> None:
        """Add collected data to the engagement."""
        pass

    @abstractmethod
    async def set_mode(self, mode: str) -> None:
        """Set the current engagement mode."""
        pass

    @abstractmethod
    async def add_target(self, target: Target) -> None:
        """Add a target to the engagement."""
        pass

    @abstractmethod
    async def remove_target(self, target_scope: str) -> None:
        """Remove a target from the engagement."""
        pass

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the state manager."""
        pass

    @abstractmethod
    async def add_command_to_history(self, command: str) -> None:
        """Add a command to the session history."""
        pass


class InMemoryStateManager(StateManager):
    """In-memory implementation of state management."""

    def __init__(self, event_bus: EventBus | None = None) -> None:
        self._state = EngagementState(
            id="default",
            name="Default Engagement",
            session_metadata=SessionMetadata(
                session_id="default",
                engagement_name="Default Engagement",
                current_mode="recon",
                notes=None,
                total_commands=0,
                total_hosts_discovered=0,
                total_findings=0,
            ),
        )
        self._event_bus = event_bus or EventBus()
        # Track reported vulnerabilities to avoid duplicates
        self._reported_vulns: set[str] = set()

    async def get_current_state(self) -> EngagementState:
        """Get the current engagement state."""
        return self._state

    def get_current_state_sync(self) -> EngagementState:
        """Get the current engagement state synchronously."""
        return self._state

    async def update_hosts(self, hosts: list[Host]) -> None:
        """Update host information with merge logic."""
        for host in hosts:
            # Find existing host by IP address instead of ID
            existing_host = None
            for _host_id, h in self._state.hosts.items():
                if h.ip_address == host.ip_address:
                    existing_host = h
                    break

            if existing_host:
                # Update existing host
                existing_host.last_seen = host.discovered_at

                # Merge services, avoiding duplicates
                existing_service_keys = {(s.port, s.protocol) for s in existing_host.services}
                for service in host.services:
                    if (service.port, service.protocol) not in existing_service_keys:
                        existing_host.services.append(service)

                # Update OS info if more recent or more confident
                if host.os_info and (
                    not existing_host.os_info
                    or (
                        host.os_confidence
                        and existing_host.os_confidence
                        and host.os_confidence > existing_host.os_confidence
                    )
                ):
                    existing_host.os_info = host.os_info
                    existing_host.os_confidence = host.os_confidence

                # Update status to most recent
                if host.status != "unknown":
                    existing_host.status = host.status

                # Merge hostnames
                for hostname in host.hostnames:
                    if hostname not in existing_host.hostnames:
                        existing_host.hostnames.append(hostname)

                # Update MAC address if available
                if host.mac_address and not existing_host.mac_address:
                    existing_host.mac_address = host.mac_address

                # Publish event with the existing host
                await self._event_bus.publish(HostDiscovered(host=existing_host))
            else:
                # Add new host
                self._state.hosts[host.id] = host

                # Publish host discovered event
                await self._event_bus.publish(HostDiscovered(host=host))

        self._state.update_timestamp()

    async def add_finding(self, finding: Finding) -> None:
        """Add a finding to the engagement."""
        # Check for duplicate vulnerabilities
        if finding.category == "vulnerability" and finding.cve_ids:
            # Create a unique key for this vulnerability
            # Get host IP if host_id is available
            host_ip = None
            if finding.host_id and finding.host_id in self._state.hosts:
                host_ip = self._state.hosts[finding.host_id].ip_address

            vuln_key = (
                f"{finding.cve_ids[0]}:{host_ip}" if finding.cve_ids and host_ip else f"{finding.title}:{host_ip}"
            )

            # Skip if already reported
            if vuln_key in self._reported_vulns:
                return

            # Mark as reported
            self._reported_vulns.add(vuln_key)

        self._state.findings[finding.id] = finding
        self._state.session_metadata.total_findings += 1
        self._state.update_timestamp()

        # Publish finding added event
        await self._event_bus.publish(FindingAdded(finding=finding))

    async def add_collected_data(self, data: CollectedData) -> None:
        """Add collected data to the engagement."""
        self._state.collected_data[data.id] = data
        self._state.update_timestamp()

        # Publish data collected event
        await self._event_bus.publish(DataCollected(data=data))

    async def set_mode(self, mode: str) -> None:
        """Set the current engagement mode."""
        old_mode = self._state.session_metadata.current_mode
        self._state.change_mode(mode)

        # Publish mode changed event
        await self._event_bus.publish(ModeChanged(old_mode=old_mode, new_mode=mode))

    async def add_target(self, target: Target) -> None:
        """Add a target to the engagement."""
        self._state.targets[target.id] = target
        self._state.update_timestamp()

    async def remove_target(self, target_scope: str) -> None:
        """Remove a target from the engagement."""
        target_to_remove = None
        for target_id, target in self._state.targets.items():
            if target.scope == target_scope:
                target_to_remove = target_id
                break

        if target_to_remove is None:
            raise ValueError(f"Target '{target_scope}' not found in scope")

        del self._state.targets[target_to_remove]
        self._state.update_timestamp()

    @property
    def event_bus(self) -> EventBus:
        """Get the event bus instance."""
        return self._event_bus

    async def initialize(self) -> None:
        """Initialize the state manager."""
        pass

    async def add_command_to_history(self, command: str) -> None:
        """Add a command to the session history."""
        if self._state.session_metadata:
            self._state.session_metadata.add_command(command)
            self._state.update_timestamp()
