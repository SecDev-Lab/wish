"""State management integration tests using HeadlessWish."""

import os
import sys

import pytest
from wish_cli.headless import EventType, HeadlessWish

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from fixtures import MockEventCollector, setup_mocks


class TestStateManagementIntegration:
    """Test state management through HeadlessWish SDK."""

    @pytest.mark.asyncio
    async def test_basic_state_operations(self):
        """Test basic state management operations."""
        # Initialize HeadlessWish with mocks
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        # Start session
        session = await wish.start_session(metadata={"test": "state_management"})

        try:
            # Initial state should be empty
            initial_state = await session.get_state()
            assert len(initial_state.targets) == 0
            assert len(initial_state.hosts) == 0
            assert len(initial_state.findings) == 0

            # Set target
            result = await session.send_prompt("set target 10.10.10.3")
            assert result.result is not None

            # Verify target was added
            state = await session.get_state()
            assert len(state.targets) == 1
            # Check targets dictionary
            assert "10.10.10.3" in state.targets
            assert state.targets["10.10.10.3"].scope == "10.10.10.3"

            # Add another target
            result = await session.send_prompt("add target 10.10.10.4")
            state = await session.get_state()
            assert len(state.targets) == 2

        finally:
            summary = await session.end()
            assert summary.session_id == session.session_id
            assert summary.prompts_executed >= 2

    @pytest.mark.asyncio
    async def test_state_persistence_across_prompts(self):
        """Test that state persists across multiple prompts."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        session = await wish.start_session()

        try:
            # Set initial targets
            await session.send_prompt("set targets 10.10.10.1-10.10.10.5")

            # Perform scan (mocked)
            result = await session.send_prompt("scan the network")

            # State should contain discovered hosts
            state = await session.get_state()
            assert len(state.hosts) > 0

            # Subsequent commands should see the same state
            result = await session.send_prompt("show current hosts")
            assert result.state_before.hosts == state.hosts

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_mode_changes(self):
        """Test engagement mode changes."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        session = await wish.start_session()

        try:
            # Initial mode should be recon
            state = await session.get_state()
            assert state.session_metadata.current_mode == "recon"

            # Change to enum mode
            await session.send_prompt("switch to enumeration mode")
            state = await session.get_state()
            assert state.session_metadata.current_mode == "enum"

            # Change to exploit mode
            await session.send_prompt("enter exploitation phase")
            state = await session.get_state()
            assert state.session_metadata.current_mode == "exploit"

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_host_and_service_discovery(self):
        """Test host and service discovery state updates."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        # Setup event collector
        collector = MockEventCollector()

        @wish.on_event(EventType.STATE_CHANGED)
        async def on_state_change(event):
            collector.collect_all(event)

        session = await wish.start_session()

        try:
            # Scan a target
            await session.send_prompt("scan 10.10.10.3 for services")

            # Check state updates
            state = await session.get_state()
            assert len(state.hosts) > 0

            # Find the discovered host
            host = next((h for h in state.hosts.values()
                        if h.ip_address == "10.10.10.3"), None)
            assert host is not None
            assert len(host.services) > 0

            # Verify services were discovered
            service_ports = [s.port for s in host.services]
            assert 22 in service_ports  # SSH
            assert 445 in service_ports  # SMB

            # Check state change events
            state_events = collector.get_events_by_type(EventType.STATE_CHANGED.value)
            assert len(state_events) > 0

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_finding_management(self):
        """Test finding creation and management."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        session = await wish.start_session()

        try:
            # First scan to discover hosts
            await session.send_prompt("scan 10.10.10.3")

            # Check for vulnerabilities
            await session.send_prompt("check for Samba vulnerabilities")

            # Findings should be created
            state = await session.get_state()
            assert len(state.findings) > 0

            # Check finding details
            finding = next(iter(state.findings.values()))
            assert finding.severity in ["critical", "high", "medium", "low"]
            assert finding.category == "vulnerability"
            assert finding.host_id is not None

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_command_history(self):
        """Test command history tracking."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        session = await wish.start_session()

        try:
            # Execute several commands
            commands = [
                "set target 10.10.10.3",
                "scan the target",
                "enumerate services",
                "check for vulnerabilities"
            ]

            for cmd in commands:
                await session.send_prompt(cmd)

            # Get final state
            state = await session.get_state()

            # Command history should be maintained
            assert len(state.session_metadata.command_history) >= len(commands)

            # Recent commands should match
            recent_commands = state.session_metadata.command_history[-len(commands):]
            assert recent_commands == commands

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_state_snapshots(self):
        """Test state snapshots in prompt results."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        session = await wish.start_session()

        try:
            # Initial state
            result1 = await session.send_prompt("set target 10.10.10.3")

            # State before should be empty
            assert len(result1.state_before.targets) == 0
            # State after should have the target
            assert len(result1.state_after.targets) == 1

            # Second command
            result2 = await session.send_prompt("scan the target")

            # State before should have the target
            assert len(result2.state_before.targets) == 1
            # State after should have hosts
            assert len(result2.state_after.hosts) > 0

            # Verify state progression
            assert result1.state_after.targets == result2.state_before.targets

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_concurrent_state_updates(self):
        """Test handling of concurrent state updates."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        session = await wish.start_session()

        try:
            # Set multiple targets
            await session.send_prompt("set targets 10.10.10.1-10.10.10.10")

            # Simulate concurrent scans (in reality these would be async)
            # The mock will handle them sequentially
            await session.send_prompt("scan all targets simultaneously")

            # All hosts should be discovered
            state = await session.get_state()
            assert len(state.hosts) > 0

            # Each host should have consistent state
            for host in state.hosts.values():
                assert host.ip_address is not None
                assert host.discovered_by is not None
                assert isinstance(host.services, list)

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_error_state_recovery(self):
        """Test state consistency after errors."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        # Collect errors
        collector = MockEventCollector()

        @wish.on_event(EventType.ERROR_OCCURRED)
        async def on_error(event):
            collector.collect_error(event)

        session = await wish.start_session()

        try:
            # Set valid target
            await session.send_prompt("set target 10.10.10.3")
            state_before_error = await session.get_state()

            # Try invalid operation
            await session.send_prompt("scan invalid.target.local")

            # State should remain consistent
            state_after_error = await session.get_state()
            assert state_after_error.targets == state_before_error.targets

            # Error should be recorded
            assert len(collector.errors) > 0

            # Should be able to continue normally
            result = await session.send_prompt("scan the valid target")
            assert result.result is not None

        finally:
            await session.end()
