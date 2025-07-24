"""E2E test for slash command integration."""


import pytest
from fixtures import setup_mocks
from wish_cli.headless import EventType, HeadlessWish


@pytest.mark.asyncio
class TestSlashCommandsIntegration:
    """Test all slash commands required for the demo scenario."""

    @pytest.fixture
    async def wish(self):
        """Create HeadlessWish instance with auto-approve."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        # Track events for debugging
        events = []

        @wish.on_event(EventType.STATE_CHANGED)
        async def on_state_change(event):
            events.append({
                "type": "state_changed",
                "timestamp": event.timestamp
            })

        wish._test_events = events
        return wish

    async def test_scope_command_workflow(self, wish):
        """Test /scope command workflow: add, list, remove."""
        session = await wish.start_session(metadata={
            "test": "scope_command_workflow"
        })

        try:
            # Test /scope with no targets
            result = await session.send_prompt("/scope")
            assert "scope" in result.result.lower() or "no targets" in result.result.lower()

            # Test /scope add
            target_ip = "10.10.10.3"
            result = await session.send_prompt(f"/scope add {target_ip}")

            # Verify target was added
            state = result.state_after
            assert state.targets is not None
            assert len(state.targets) > 0

            # Find the target
            target_found = False
            for target in state.targets.values():
                if target_ip in target.scope:
                    target_found = True
                    break
            assert target_found, f"Target {target_ip} not found in scope"

            # Test /scope list (implicit)
            result = await session.send_prompt("/scope")
            assert target_ip in result.result

            # Test /scope remove
            result = await session.send_prompt(f"/scope remove {target_ip}")

            # Verify target was removed
            state = result.state_after
            if state.targets:
                for target in state.targets.values():
                    assert target_ip not in target.scope

        finally:
            await session.end()

    async def test_status_command_display(self, wish):
        """Test /status command displays engagement state properly."""
        session = await wish.start_session(metadata={
            "test": "status_command_display"
        })

        try:
            # Set up some test data
            await session.send_prompt("/scope add 10.10.10.3")

            # Simulate adding a host with services
            # This would normally come from a scan
            result = await session.send_prompt("/status")

            # Check that status command returns structured information
            status_output = result.result
            assert status_output is not None

            # Should show targets section
            assert "10.10.10.3" in status_output or "target" in status_output.lower()

        finally:
            await session.end()

    async def test_findings_command_workflow(self, wish):
        """Test /findings command: list and add."""
        session = await wish.start_session(metadata={
            "test": "findings_command_workflow"
        })

        try:
            # Test /findings with no findings
            result = await session.send_prompt("/findings")
            initial_output = result.result.lower()
            assert "findings" in initial_output or "no findings" in initial_output

            # Test /findings add
            finding_desc = "Test vulnerability: Remote code execution in service X"
            result = await session.send_prompt(f"/findings add {finding_desc}")

            # Verify finding was added
            state = result.state_after
            assert state.findings is not None
            assert len(state.findings) > 0

            # Check finding details
            finding = next(iter(state.findings.values()))
            assert finding_desc in finding.description or finding_desc in finding.title

            # Test /findings list
            result = await session.send_prompt("/findings")
            assert finding_desc in result.result or "remote code execution" in result.result.lower()

        finally:
            await session.end()

    async def test_slash_command_aliases(self, wish):
        """Test that command aliases work properly."""
        session = await wish.start_session(metadata={
            "test": "command_aliases"
        })

        try:
            # Test /s alias for /status
            result = await session.send_prompt("/s")
            assert result.result is not None
            assert "error" not in result.result.lower()

            # Test /f alias for /findings
            result = await session.send_prompt("/f")
            assert result.result is not None
            assert "error" not in result.result.lower()

            # Test /j alias for /jobs
            result = await session.send_prompt("/j")
            assert result.result is not None
            assert "error" not in result.result.lower()

        finally:
            await session.end()

    async def test_demo_scenario_commands(self, wish):
        """Test the exact command sequence from the demo scenario."""
        session = await wish.start_session(metadata={
            "test": "demo_scenario_commands"
        })

        try:
            # ACT 1: Initial setup
            result = await session.send_prompt("/scope add 10.10.10.3")
            assert "added" in result.result.lower() or "scope" in result.result.lower()

            # Verify we can check status
            result = await session.send_prompt("/status")
            assert "10.10.10.3" in result.result

            # ACT 3: Findings management
            # Add a demo finding
            cve_finding = "CVE-2007-2447: Samba Username Map Script Remote Command Execution"
            result = await session.send_prompt(f"/findings add {cve_finding}")

            # Verify findings display
            result = await session.send_prompt("/findings")
            assert "CVE-2007-2447" in result.result or "samba" in result.result.lower()

            # Final status check
            result = await session.send_prompt("/status")
            state = result.state_after

            # Verify complete state
            assert len(state.targets) > 0
            assert len(state.findings) > 0

        finally:
            await session.end()
