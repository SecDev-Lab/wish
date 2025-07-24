"""E2E tests for new Sliver stager commands."""

from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from fixtures import setup_mocks
from wish_c2 import StagerListener
from wish_cli.headless.client import HeadlessWish


@pytest.mark.asyncio
class TestSliverStagerE2E:
    """Test new Sliver stager command functionality end-to-end."""

    @pytest.fixture
    async def wish_with_mock_sliver(self):
        """Create HeadlessWish instance with mocked Sliver C2."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        # Create mock C2 connector
        mock_c2 = AsyncMock()
        mock_c2.is_connected = AsyncMock(return_value=True)
        mock_c2.get_server = AsyncMock(return_value="localhost:31337")

        # Mock stager operations
        mock_listener = StagerListener(
            id="stg-test123",
            name="default",
            url="http://10.10.14.2:54321",
            host="10.10.14.2",
            port=54321,
            protocol="http",
            status="running",
            started_at=datetime.now()
        )
        mock_c2.start_stager_listener = AsyncMock(return_value=(mock_listener, "stager_code"))
        mock_c2.list_stager_listeners = AsyncMock(return_value=[mock_listener])
        mock_c2.stop_stager_listener = AsyncMock(return_value=True)

        # Re-initialize CommandDispatcher with mock C2
        from wish_cli.core.command_dispatcher import CommandDispatcher
        wish.command_dispatcher = CommandDispatcher(
            ui_manager=wish.ui_manager,
            state_manager=wish.state_manager,
            session_manager=wish.session_manager,
            conversation_manager=wish.conversation_manager,
            plan_generator=wish.plan_generator,
            tool_executor=wish.tool_executor,
            c2_connector=mock_c2,
        )

        # Update UI manager's reference
        wish.ui_manager.set_command_dispatcher(wish.command_dispatcher)

        return wish

    async def test_stager_help(self, wish_with_mock_sliver):
        """Test /sliver stager help command."""
        wish = wish_with_mock_sliver
        session = await wish.start_session(metadata={
            "test": "stager_help",
            "feature": "new_stager_commands"
        })

        try:
            # Test help with no args
            result = await session.send_prompt("/sliver stager")
            assert "Stager Commands" in result.result
            assert "start [--host <IP>]" in result.result
            assert "stop <listener-id>" in result.result
            assert "list" in result.result
            assert "create <listener-id> --type" in result.result

            # Test explicit help
            result = await session.send_prompt("/sliver stager help")
            assert "Stager Commands" in result.result

        finally:
            await session.end()

    async def test_stager_start(self, wish_with_mock_sliver):
        """Test /sliver stager start command."""
        wish = wish_with_mock_sliver
        session = await wish.start_session(metadata={
            "test": "stager_start",
            "feature": "new_stager_commands"
        })

        try:
            # Start stager listener
            result = await session.send_prompt("/sliver stager start --host 10.10.14.2")
            assert "Stager listener started" in result.result
            assert "stg-test123" in result.result
            assert "http://10.10.14.2:54321" in result.result
            assert "Default Stagers:" in result.result
            assert "import urllib2,platform" in result.result

            # Test with specific port
            result = await session.send_prompt("/sliver stager start --host 192.168.1.100 --port 8080")
            assert "Starting stager listener" in result.result

        finally:
            await session.end()

    async def test_stager_list(self, wish_with_mock_sliver):
        """Test /sliver stager list command."""
        wish = wish_with_mock_sliver
        session = await wish.start_session(metadata={
            "test": "stager_list",
            "feature": "new_stager_commands"
        })

        try:
            # Start a listener first
            await session.send_prompt("/sliver stager start --host 10.10.14.2")

            # List stager listeners
            result = await session.send_prompt("/sliver stager list")
            assert "Active Stager Listeners" in result.result
            assert "stg-test123" in result.result
            assert "http://10.10.14.2:54321" in result.result
            assert "running" in result.result

        finally:
            await session.end()

    async def test_stager_create(self, wish_with_mock_sliver):
        """Test /sliver stager create command."""
        wish = wish_with_mock_sliver
        session = await wish.start_session(metadata={
            "test": "stager_create",
            "feature": "new_stager_commands"
        })

        try:
            # Start a listener first
            await session.send_prompt("/sliver stager start --host 10.10.14.2")

            # Create bash stager
            result = await session.send_prompt("/sliver stager create stg-test123 --type bash")
            assert "Bash Stager:" in result.result
            assert "curl -s" in result.result
            assert "/s?o=" in result.result

            # Create powershell stager
            result = await session.send_prompt("/sliver stager create stg-test123 --type powershell")
            assert "Powershell Stager:" in result.result
            assert "IEX(New-Object Net.WebClient)" in result.result

            # Test invalid type
            result = await session.send_prompt("/sliver stager create stg-test123 --type invalid")
            assert "Invalid stager type" in result.result

        finally:
            await session.end()

    async def test_stager_stop(self, wish_with_mock_sliver):
        """Test /sliver stager stop command."""
        wish = wish_with_mock_sliver
        session = await wish.start_session(metadata={
            "test": "stager_stop",
            "feature": "new_stager_commands"
        })

        try:
            # Start a listener first
            await session.send_prompt("/sliver stager start --host 10.10.14.2")

            # Stop the listener
            result = await session.send_prompt("/sliver stager stop stg-test123")
            assert "Stopped stager listener: stg-test123" in result.result

            # Test stopping non-existent listener
            result = await session.send_prompt("/sliver stager stop invalid-id")
            # Should handle gracefully
            assert "Failed to stop" in result.result or "Stopped" in result.result

        finally:
            await session.end()

    async def test_stager_workflow(self, wish_with_mock_sliver):
        """Test complete stager workflow."""
        wish = wish_with_mock_sliver
        session = await wish.start_session(metadata={
            "test": "stager_workflow",
            "feature": "new_stager_commands"
        })

        try:
            # 1. Start stager listener
            result = await session.send_prompt("/sliver stager start --host 10.10.14.2")
            assert "Stager listener started" in result.result
            assert "python -c" in result.result

            # 2. List active listeners
            result = await session.send_prompt("/sliver stager list")
            assert "Active Stager Listeners" in result.result
            assert "stg-test123" in result.result

            # 3. Create additional stager types
            result = await session.send_prompt("/sliver stager create stg-test123 --type bash")
            assert "Bash Stager:" in result.result

            result = await session.send_prompt("/sliver stager create stg-test123 --type powershell")
            assert "Powershell Stager:" in result.result

            # 4. Stop the listener
            result = await session.send_prompt("/sliver stager stop stg-test123")
            assert "Stopped stager listener" in result.result

        finally:
            await session.end()

    async def test_stager_error_handling(self, wish_with_mock_sliver):
        """Test stager command error handling."""
        wish = wish_with_mock_sliver
        session = await wish.start_session(metadata={
            "test": "stager_errors",
            "feature": "error_handling"
        })

        try:
            # Start without host
            result = await session.send_prompt("/sliver stager start")
            assert "Usage:" in result.result
            assert "--host <IP>" in result.result

            # Stop without ID
            result = await session.send_prompt("/sliver stager stop")
            assert "Usage:" in result.result
            assert "<listener-id>" in result.result

            # Create without required args
            result = await session.send_prompt("/sliver stager create")
            assert "Usage:" in result.result

            # Create without type
            result = await session.send_prompt("/sliver stager create stg-test123")
            assert "Usage:" in result.result
            assert "--type <type>" in result.result

            # Unknown subcommand
            result = await session.send_prompt("/sliver stager invalid")
            assert "Unknown stager command" in result.result

        finally:
            await session.end()

    async def test_htb_lame_stager_scenario(self, wish_with_mock_sliver):
        """Test HTB Lame scenario with new stager commands."""
        wish = wish_with_mock_sliver
        session = await wish.start_session(metadata={
            "test": "htb_lame_stager",
            "feature": "complete_scenario"
        })

        try:
            # Set up HTB Lame target
            await session.send_prompt("/scope add 10.10.10.3")

            # Start stager listener for HTB Lame
            result = await session.send_prompt("/sliver stager start --host 10.10.14.2")
            assert "Stager listener started" in result.result
            assert "Default Stagers:" in result.result

            # Verify Python stager is HTB Lame compatible
            assert "python -c" in result.result
            assert "urllib2" in result.result  # Python 2 compatible
            assert "platform" in result.result  # Environment detection

            # User would now copy the stager to HTB Lame
            # In this test, we just verify the stager was generated

            # Create alternative stagers if needed
            result = await session.send_prompt("/sliver stager create stg-test123 --type bash")
            assert "curl -s" in result.result

            # Add finding about successful C2 setup
            await session.send_prompt(
                "/findings add Successfully deployed Sliver stager on HTB Lame using Python urllib2"
            )

            # Verify workflow completion
            result = await session.send_prompt("/findings")
            assert "Sliver stager" in result.result

        finally:
            await session.end()
