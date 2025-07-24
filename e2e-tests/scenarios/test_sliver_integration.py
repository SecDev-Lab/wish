"""E2E tests for Sliver C2 integration."""

import asyncio

import pytest
from fixtures import setup_mocks
from wish_cli.headless.client import HeadlessWish


@pytest.mark.asyncio
class TestSliverIntegration:
    """Test Sliver C2 integration features."""

    @pytest.fixture
    async def wish_with_sliver(self):
        """Create HeadlessWish instance with Sliver C2 configured."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        # NOTE: Mock mode has been removed in Phase 2
        # E2E tests now require actual Sliver C2 server
        # This test may need to be skipped if Sliver is not available
        pytest.skip("Sliver C2 mock mode removed in Phase 2 - requires real Sliver server")

        # Re-initialize CommandDispatcher with C2 connector
        from wish_cli.core.command_dispatcher import CommandDispatcher
        wish.command_dispatcher = CommandDispatcher(
            ui_manager=wish.ui_manager,
            state_manager=wish.state_manager,
            session_manager=wish.session_manager,
            conversation_manager=wish.conversation_manager,
            plan_generator=wish.plan_generator,
            tool_executor=wish.tool_executor,
            c2_connector=c2_connector,
        )

        # Update UI manager's reference
        wish.ui_manager.set_command_dispatcher(wish.command_dispatcher)

        return wish

    async def test_sliver_status_command(self, wish_with_sliver):
        """Test /sliver status command."""
        wish = wish_with_sliver
        session = await wish.start_session(metadata={
            "test": "sliver_status",
            "feature": "c2_integration"
        })

        try:
            # Check C2 status
            result = await session.send_prompt("/sliver status")
            assert "Connected" in result.result
            assert "localhost:31337" in result.result
            assert "1 active" in result.result  # One demo session

        finally:
            await session.end()

    async def test_sliver_implants_command(self, wish_with_sliver):
        """Test /sliver implants command."""
        wish = wish_with_sliver
        session = await wish.start_session(metadata={
            "test": "sliver_implants",
            "feature": "c2_integration"
        })

        try:
            # List implants
            result = await session.send_prompt("/sliver implants")
            assert "FANCY_TIGER" in result.result
            assert "10.10.10.3" in result.result
            assert "linux/amd64" in result.result
            assert "root" in result.result
            assert "active" in result.result.lower()

        finally:
            await session.end()

    async def test_sliver_shell_command(self, wish_with_sliver):
        """Test /sliver shell command interaction."""
        wish = wish_with_sliver
        session = await wish.start_session(metadata={
            "test": "sliver_shell",
            "feature": "c2_integration"
        })

        try:
            # Start shell session
            result = await session.send_prompt("/sliver shell FANCY_TIGER")
            assert "Starting shell" in result.result
            assert "Connected to FANCY_TIGER" in result.result

            # Note: In a real E2E test, we would need to simulate
            # the interactive shell mode. For now, we just verify
            # that the shell command is accepted and initialized.

        finally:
            await session.end()

    async def test_sliver_execute_command(self, wish_with_sliver):
        """Test /sliver execute command."""
        wish = wish_with_sliver
        session = await wish.start_session(metadata={
            "test": "sliver_execute",
            "feature": "c2_integration"
        })

        try:
            # Execute single command
            result = await session.send_prompt("/sliver execute FANCY_TIGER whoami")
            assert "root" in result.result

            # Execute another command
            result = await session.send_prompt("/sliver execute FANCY_TIGER cat root.txt")
            assert "92caac3be140ef409e45721348a4e9df" in result.result

        finally:
            await session.end()

    async def test_htb_lame_with_sliver(self, wish_with_sliver):
        """Test HTB Lame demo scenario with Sliver integration."""
        wish = wish_with_sliver
        session = await wish.start_session(metadata={
            "test": "htb_lame_sliver",
            "feature": "complete_demo"
        })

        try:
            # ACT 1: Discovery
            await session.send_prompt("/scope add 10.10.10.3")
            await session.send_prompt("scan 10.10.10.3")
            await asyncio.sleep(0.5)  # Wait for scan

            # ACT 2: Exploitation (simulated)
            await session.send_prompt("check the samba vulnerability")
            await asyncio.sleep(0.5)

            # ACT 3: Post-exploitation with Sliver
            result = await session.send_prompt("/sliver status")
            assert "Connected" in result.result

            result = await session.send_prompt("/sliver implants")
            assert "FANCY_TIGER" in result.result
            assert "10.10.10.3" in result.result

            # Execute commands via Sliver
            result = await session.send_prompt("/sliver execute FANCY_TIGER whoami")
            assert "root" in result.result

            result = await session.send_prompt("/sliver execute FANCY_TIGER cat root.txt")
            assert "92caac3be140ef409e45721348a4e9df" in result.result

            # Add finding
            await session.send_prompt(
                "/findings add CVE-2007-2447: Samba RCE exploited, root access obtained via Sliver C2"
            )

            # Final status
            result = await session.send_prompt("/status")
            assert "10.10.10.3" in result.result

            result = await session.send_prompt("/findings")
            assert "CVE-2007-2447" in result.result
            assert "sliver" in result.result.lower() or "root access" in result.result.lower()

        finally:
            await session.end()

    async def test_sliver_error_handling(self, wish_with_sliver):
        """Test Sliver error handling."""
        wish = wish_with_sliver
        session = await wish.start_session(metadata={
            "test": "sliver_errors",
            "feature": "error_handling"
        })

        try:
            # Try to execute on non-existent session
            result = await session.send_prompt("/sliver execute INVALID_SESSION whoami")
            assert "not found" in result.result.lower()

            # Try shell with invalid session
            result = await session.send_prompt("/sliver shell INVALID_SESSION")
            assert "not found" in result.result.lower()

            # Try invalid sliver subcommand
            result = await session.send_prompt("/sliver invalid_command")
            assert "unknown" in result.result.lower()

        finally:
            await session.end()

    @pytest.mark.parametrize("command,expected", [
        ("whoami", "root"),
        ("id", "uid=0(root)"),
        ("pwd", "/root"),
        ("hostname", "lame"),
        ("uname -a", "Linux lame"),
        ("ls", "root.txt"),
        ("cat user.txt", "69454a937d94f5f0225ea00acd2e84c5"),
    ])
    async def test_sliver_command_responses(self, wish_with_sliver, command, expected):
        """Test various Sliver command responses."""
        wish = wish_with_sliver
        session = await wish.start_session(metadata={
            "test": "sliver_commands",
            "command": command
        })

        try:
            result = await session.send_prompt(f"/sliver execute FANCY_TIGER {command}")
            assert expected in result.result

        finally:
            await session.end()
