"""Integration tests with real Sliver C2 server."""

import asyncio
import time
from pathlib import Path

import pytest

from wish_c2 import create_c2_connector
from wish_c2.exceptions import (
    C2Error,
    SessionNotFoundError,
)


def has_sliver_config():
    """Check if Sliver test config exists."""
    config_path = Path("~/.sliver-client/configs/wish-test.cfg").expanduser()
    return config_path.exists()


@pytest.mark.integration
@pytest.mark.requires_sliver
@pytest.mark.skipif(not has_sliver_config(), reason="Sliver test config not found")
class TestRealSliverIntegration:
    """Integration tests with real Sliver C2 server."""

    @pytest.fixture
    async def real_connector(self):
        """Create real Sliver connector with SSL verification disabled for testing."""
        config_path = Path("~/.sliver-client/configs/wish-test.cfg").expanduser()
        connector = create_c2_connector(
            "sliver",
            mode="real",
            config={
                "config_path": str(config_path),
                "ssl_options": {
                    "skip_verify": True  # For test environment only - DO NOT use in production
                },
            },
        )
        yield connector
        # Cleanup
        if connector.connected:
            await connector.disconnect()

    async def test_real_connection(self, real_connector):
        """Test actual connection to Sliver server."""
        # Connect
        result = await real_connector.connect()
        assert result is True
        assert real_connector.connected is True

        # Check server info
        assert real_connector.server in ["localhost:31337", "127.0.0.1:31337", "[::1]:31337"]

        # Disconnect
        await real_connector.disconnect()
        assert real_connector.connected is False

    async def test_reconnection(self, real_connector):
        """Test connection resilience."""
        # Connect, disconnect, reconnect
        await real_connector.connect()
        await real_connector.disconnect()

        # Should be able to reconnect
        result = await real_connector.connect()
        assert result is True
        assert real_connector.connected is True

    async def test_get_sessions_empty(self, real_connector):
        """Test getting sessions when none exist."""
        await real_connector.connect()

        sessions = await real_connector.get_sessions()
        assert isinstance(sessions, list)
        # Sessions might be empty if no implant is running
        print(f"Found {len(sessions)} active sessions")

    async def test_session_not_found_error(self, real_connector):
        """Test error handling for non-existent session."""
        await real_connector.connect()

        # Try to execute command on non-existent session
        with pytest.raises(SessionNotFoundError):
            await real_connector.execute_command("non-existent-session", "whoami")

    async def test_invalid_command_with_session(self, real_connector):
        """Test command execution with existing session if available."""
        await real_connector.connect()

        sessions = await real_connector.get_sessions()
        if not sessions:
            pytest.skip("No active sessions available for testing")

        session = sessions[0]
        print(f"Testing with session: {session.name} ({session.id[:8]}...)")

        # Execute a simple command
        result = await real_connector.execute_command(session.id, "echo 'Hello from Sliver'")
        assert result.stdout.strip() == "'Hello from Sliver'"
        assert result.exit_code == 0

    async def test_multiple_commands(self, real_connector):
        """Test executing multiple commands in sequence."""
        await real_connector.connect()

        sessions = await real_connector.get_sessions()
        if not sessions:
            pytest.skip("No active sessions available for testing")

        session = sessions[0]
        commands = ["pwd", "whoami", "date", "echo $SHELL"]

        for cmd in commands:
            result = await real_connector.execute_command(session.id, cmd)
            assert result.exit_code == 0
            assert result.stdout  # Should have output
            print(f"{cmd}: {result.stdout.strip()}")

    async def test_command_timeout(self, real_connector):
        """Test command execution timeout handling."""
        await real_connector.connect()

        sessions = await real_connector.get_sessions()
        if not sessions:
            pytest.skip("No active sessions available for testing")

        session = sessions[0]

        # This should complete normally
        start = time.time()
        result = await real_connector.execute_command(session.id, "sleep 1 && echo done")
        duration = time.time() - start

        assert result.exit_code == 0
        assert "done" in result.stdout
        assert duration < 5  # Should complete in reasonable time

    async def test_interactive_shell_creation(self, real_connector):
        """Test creating interactive shell."""
        await real_connector.connect()

        sessions = await real_connector.get_sessions()
        if not sessions:
            pytest.skip("No active sessions available for testing")

        session = sessions[0]

        # Create interactive shell
        shell = await real_connector.start_interactive_shell(session.id)
        assert shell is not None
        assert shell.active is True
        assert shell.session.id == session.id

        # Execute command in shell
        output = await shell.execute("echo 'Interactive shell test'")
        assert "Interactive shell test" in output

        # Close shell
        await shell.close()
        assert shell.active is False

    async def test_session_persistence(self, real_connector):
        """Test that sessions persist across connections."""
        # First connection
        await real_connector.connect()
        sessions1 = await real_connector.get_sessions()
        session_ids1 = {s.id for s in sessions1}
        await real_connector.disconnect()

        # Wait a bit
        await asyncio.sleep(1)

        # Second connection
        await real_connector.connect()
        sessions2 = await real_connector.get_sessions()
        session_ids2 = {s.id for s in sessions2}

        # Sessions should be the same (if any exist)
        if session_ids1 and session_ids2:
            assert session_ids1 == session_ids2

    async def test_safe_mode_with_real_server(self):
        """Test safe mode with real Sliver server."""
        config_path = Path("~/.sliver-client/configs/wish-test.cfg").expanduser()

        # Create safe connector
        safe_connector = create_c2_connector(
            "sliver",
            mode="safe",
            config={
                "config_path": str(config_path),
                "safety": {"sandbox_mode": True, "allowed_commands": ["echo", "pwd", "whoami"], "read_only": True},
                "ssl_options": {
                    "skip_verify": True  # For test environment only - DO NOT use in production
                },
            },
        )

        try:
            await safe_connector.connect()
            sessions = await safe_connector.get_sessions()

            if sessions:
                session = sessions[0]

                # Allowed command should work
                result = await safe_connector.execute_command(session.id, "echo safe")
                assert result.exit_code == 0

                # Disallowed command should fail
                from wish_c2.exceptions import SecurityError

                with pytest.raises(SecurityError):
                    await safe_connector.execute_command(session.id, "cat /etc/passwd")

                # Write command should fail in read-only mode
                with pytest.raises(SecurityError):
                    await safe_connector.execute_command(session.id, "touch test.txt")

        finally:
            if safe_connector.connected:
                await safe_connector.disconnect()


@pytest.mark.integration
@pytest.mark.requires_sliver
class TestSliverConnectionErrors:
    """Test error handling without active Sliver server."""

    async def test_connection_failure_wrong_port(self):
        """Test connection to wrong port."""
        # Should fail when creating connector with non-existent config
        with pytest.raises(C2Error):
            create_c2_connector(
                "sliver", mode="real", config={"config_path": str(Path.home() / ".test-fake-config.cfg")}
            )

    async def test_connection_with_invalid_config(self):
        """Test connection with invalid config file."""
        # Create a fake config file
        fake_config = Path.home() / ".test-invalid-sliver.cfg"
        fake_config.write_text('{"invalid": "config"}')

        try:
            connector = create_c2_connector("sliver", mode="real", config={"config_path": str(fake_config)})

            # Should fail to connect
            with pytest.raises(C2Error):  # Should raise C2Error for connection issues
                await connector.connect()

        finally:
            fake_config.unlink(missing_ok=True)
