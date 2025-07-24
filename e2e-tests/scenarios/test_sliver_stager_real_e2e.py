"""E2E tests for Sliver stager with real connector."""

import asyncio
import urllib.error
import urllib.request
from pathlib import Path

import pytest
from fixtures import setup_mocks
from wish_c2.sliver.connector import RealSliverConnector
from wish_cli.headless.client import HeadlessWish


@pytest.mark.asyncio
@pytest.mark.skipif(
    not (Path.home() / ".sliver-client" / "configs" / "wish-test.cfg").exists(),
    reason="Sliver test config not found"
)
class TestSliverStagerRealE2E:
    """Test Sliver stager with real connector."""

    @pytest.fixture
    async def wish_with_real_sliver(self):
        """Create HeadlessWish instance with real Sliver C2."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        # Create real C2 connector
        config_path = Path.home() / ".sliver-client" / "configs" / "wish-test.cfg"
        real_c2 = RealSliverConnector(config_path)

        # Connect to Sliver
        await real_c2.connect()

        # Re-initialize CommandDispatcher with real C2
        from wish_cli.core.command_dispatcher import CommandDispatcher
        wish.command_dispatcher = CommandDispatcher(
            ui_manager=wish.ui_manager,
            state_manager=wish.state_manager,
            session_manager=wish.session_manager,
            conversation_manager=wish.conversation_manager,
            plan_generator=wish.plan_generator,
            tool_executor=wish.tool_executor,
            c2_connector=real_c2,
        )

        # Update UI manager's reference
        wish.ui_manager.set_command_dispatcher(wish.command_dispatcher)

        yield wish

        # Cleanup
        await real_c2.disconnect()

    async def test_real_stager_start_and_download(self, wish_with_real_sliver):
        """Test starting real stager and downloading implant."""
        wish = wish_with_real_sliver
        session = await wish.start_session(metadata={
            "test": "real_stager_start",
            "feature": "real_sliver_integration"
        })

        try:
            # Start stager listener
            result = await session.send_prompt("/sliver stager start --host 127.0.0.1 --port 48080")
            assert "Stager listener started" in result.result
            assert "http://127.0.0.1:48080" in result.result

            # Extract listener ID from result
            import re
            match = re.search(r'stg-[a-zA-Z0-9]+', result.result)
            assert match, "Listener ID not found in output"
            listener_id = match.group(0)

            # Wait a moment for server to fully start
            await asyncio.sleep(1)

            # Test downloading implant
            # Test stager endpoint
            try:
                with urllib.request.urlopen('http://127.0.0.1:48080/s?o=linux&a=64') as response:
                    assert response.status == 200
                    stager_content = response.read().decode('utf-8')
                    assert "[*] Stager starting..." in stager_content
                    assert "urllib2" in stager_content
            except urllib.error.URLError as e:
                pytest.fail(f"Failed to download stager: {e}")

            # Test implant download endpoint
            try:
                with urllib.request.urlopen('http://127.0.0.1:48080/implant/stager_linux_amd64') as response:
                    assert response.status == 200
                    implant_data = response.read()

                    # Check if we got real implant or fallback
                    if len(implant_data) > 1000000:  # Real implants are several MB
                        # Real Sliver implant
                        assert b"ELF" in implant_data[:4] or b"MZ" in implant_data[:2]
                        print(f"[+] Downloaded real Sliver implant: {len(implant_data)} bytes")
                    else:
                        # Fallback script
                        assert b"#!/bin/sh" in implant_data[:10]
                        print(f"[!] Got fallback script: {len(implant_data)} bytes")
                        # Check fallback content for debugging info
                        fallback_text = implant_data.decode('utf-8', errors='ignore')
                        if "FALLBACK MODE" in fallback_text:
                            print("[!] Fallback reasons in script:")
                            for line in fallback_text.split('\n'):
                                if "Possible reasons" in line or line.strip().startswith(("1.", "2.", "3.")):
                                    print(f"    {line.strip()}")
            except urllib.error.URLError as e:
                pytest.fail(f"Failed to download implant: {e}")

            # List stagers
            result = await session.send_prompt("/sliver stager list")
            assert "Active Stager Listeners" in result.result
            assert listener_id in result.result
            assert "running" in result.result

            # Stop stager
            result = await session.send_prompt(f"/sliver stager stop {listener_id}")
            assert "Stopped stager listener" in result.result

        finally:
            await session.end()

    async def test_real_stager_multiple_types(self, wish_with_real_sliver):
        """Test creating different stager types."""
        wish = wish_with_real_sliver
        session = await wish.start_session(metadata={
            "test": "real_stager_types",
            "feature": "stager_variations"
        })

        try:
            # Start stager listener
            result = await session.send_prompt("/sliver stager start --host 127.0.0.1")
            assert "Stager listener started" in result.result

            # Extract listener ID
            import re
            match = re.search(r'stg-[a-zA-Z0-9]+', result.result)
            listener_id = match.group(0)

            # Test different stager types
            stager_types = ["python", "bash", "minimal", "debug"]
            for stager_type in stager_types:
                result = await session.send_prompt(f"/sliver stager create {listener_id} --type {stager_type}")
                assert f"{stager_type.title()} Stager:" in result.result or stager_type in result.result.lower()

            # Stop stager
            await session.send_prompt(f"/sliver stager stop {listener_id}")

        finally:
            await session.end()

    async def test_real_stager_error_recovery(self, wish_with_real_sliver):
        """Test stager error handling and recovery."""
        wish = wish_with_real_sliver
        session = await wish.start_session(metadata={
            "test": "real_stager_errors",
            "feature": "error_handling"
        })

        try:
            # Try to start on privileged port (should fail or fallback to random)
            result = await session.send_prompt("/sliver stager start --host 127.0.0.1 --port 80")
            # Either fails with permission error or uses different port
            assert "Stager listener started" in result.result or "Failed" in result.result

            # Start on valid port
            result = await session.send_prompt("/sliver stager start --host 127.0.0.1 --port 58080")
            assert "Stager listener started" in result.result

            # Extract listener ID
            import re
            match = re.search(r'stg-[a-zA-Z0-9]+', result.result)
            if match:
                listener_id = match.group(0)
                # Clean up
                await session.send_prompt(f"/sliver stager stop {listener_id}")

        finally:
            await session.end()
