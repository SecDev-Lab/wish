"""Unit tests for Sliver C2 commands."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from rich.console import Console
from wish_c2 import BaseC2Connector, StagerListener

from wish_cli.commands.sliver import SliverCommand


@pytest.fixture
def mock_c2():
    """Create mock C2 connector."""
    c2 = AsyncMock(spec=BaseC2Connector)
    c2.is_connected = AsyncMock(return_value=True)
    c2.get_server = AsyncMock(return_value="localhost:31337")
    c2.get_sessions = AsyncMock(return_value=[])
    return c2


@pytest.fixture
def mock_console():
    """Create mock console."""
    return MagicMock(spec=Console)


@pytest.fixture
def sliver_command(mock_c2, mock_console):
    """Create SliverCommand instance with mocks."""
    return SliverCommand(mock_c2, mock_console)


class TestStagerCommands:
    """Test stager command functionality."""

    @pytest.mark.asyncio
    async def test_stager_help_no_args(self, sliver_command, mock_console):
        """Test stager help displayed when no arguments."""
        await sliver_command.handle_stager([])

        # Verify help panel was printed
        assert mock_console.print.called
        # Check that Panel object was passed
        call_args = mock_console.print.call_args_list
        panel_found = False
        for call in call_args:
            if len(call[0]) > 0 and hasattr(call[0][0], "__class__"):
                if call[0][0].__class__.__name__ == "Panel":
                    panel_found = True
                    break
        assert panel_found, "Panel should be printed for help"

    @pytest.mark.asyncio
    async def test_stager_help_explicit(self, sliver_command, mock_console):
        """Test stager help with explicit help command."""
        await sliver_command.handle_stager(["help"])

        # Verify help panel was printed
        assert mock_console.print.called
        # Check that Panel object was passed
        call_args = mock_console.print.call_args_list
        panel_found = False
        for call in call_args:
            if len(call[0]) > 0 and hasattr(call[0][0], "__class__"):
                if call[0][0].__class__.__name__ == "Panel":
                    panel_found = True
                    break
        assert panel_found, "Panel should be printed for help"

    @pytest.mark.asyncio
    async def test_stager_start_no_host(self, sliver_command, mock_console):
        """Test stager start without required host argument."""
        await sliver_command.handle_stager(["start"])

        # Should show error
        printed_content = str(mock_console.print.call_args_list)
        assert "Usage: /sliver stager start --host <IP>" in printed_content

    @pytest.mark.asyncio
    async def test_stager_start_success(self, sliver_command, mock_c2, mock_console):
        """Test successful stager start."""
        # Mock listener response
        listener = StagerListener(
            id="stg-test123",
            name="default",
            url="http://10.10.14.2:54321",
            host="10.10.14.2",
            port=54321,
            protocol="http",
            status="running",
            started_at=datetime.now(),
        )
        mock_c2.start_stager_listener = AsyncMock(return_value=(listener, "dummy_code"))

        await sliver_command.handle_stager(["start", "--host", "10.10.14.2"])

        # Verify listener was started (with progress callback)
        mock_c2.start_stager_listener.assert_called_once()
        call_args = mock_c2.start_stager_listener.call_args
        assert call_args[0][0] == "default"  # name
        assert call_args[0][1] == "10.10.14.2"  # host
        assert call_args[0][2] is None  # port
        assert call_args[0][3] == "http"  # protocol
        assert callable(call_args[0][4])  # progress_callback

        # Verify output contains expected elements
        all_printed = []
        for call in mock_console.print.call_args_list:
            if call[0]:
                all_printed.append(str(call[0][0]))
        full_output = "\n".join(all_printed)

        assert "stg-test123" in full_output
        assert "Python 2" in full_output  # Changed from "Default Stager (Python)"
        assert "import urllib2,platform" in full_output

    @pytest.mark.asyncio
    async def test_stager_start_with_port(self, sliver_command, mock_c2, mock_console):
        """Test stager start with specific port."""
        listener = StagerListener(
            id="stg-test123",
            name="default",
            url="http://10.10.14.2:8080",
            host="10.10.14.2",
            port=8080,
            protocol="http",
            status="running",
            started_at=datetime.now(),
        )
        mock_c2.start_stager_listener = AsyncMock(return_value=(listener, "dummy_code"))

        await sliver_command.handle_stager(["start", "--host", "10.10.14.2", "--port", "8080"])

        # Verify listener was started with correct port (with progress callback)
        mock_c2.start_stager_listener.assert_called_once()
        call_args = mock_c2.start_stager_listener.call_args
        assert call_args[0][0] == "default"  # name
        assert call_args[0][1] == "10.10.14.2"  # host
        assert call_args[0][2] == 8080  # port
        assert call_args[0][3] == "http"  # protocol
        assert callable(call_args[0][4])  # progress_callback

    @pytest.mark.asyncio
    async def test_stager_list_empty(self, sliver_command, mock_c2, mock_console):
        """Test stager list with no active listeners."""
        mock_c2.list_stager_listeners = AsyncMock(return_value=[])

        await sliver_command.handle_stager(["list"])

        printed_content = str(mock_console.print.call_args_list)
        assert "No active stager listeners" in printed_content

    @pytest.mark.asyncio
    async def test_stager_list_with_listeners(self, sliver_command, mock_c2, mock_console):
        """Test stager list with active listeners."""
        listeners = [
            StagerListener(
                id="stg-test1",
                name="listener1",
                url="http://10.10.14.2:54321",
                host="10.10.14.2",
                port=54321,
                protocol="http",
                status="running",
                started_at=datetime.now(),
            ),
            StagerListener(
                id="stg-test2",
                name="listener2",
                url="http://192.168.1.100:8080",
                host="192.168.1.100",
                port=8080,
                protocol="http",
                status="running",
                started_at=datetime.now(),
            ),
        ]
        mock_c2.list_stager_listeners = AsyncMock(return_value=listeners)

        await sliver_command.handle_stager(["list"])

        # Verify table was created
        table_found = False
        for call in mock_console.print.call_args_list:
            if len(call[0]) > 0 and hasattr(call[0][0], "__class__"):
                if call[0][0].__class__.__name__ == "Table":
                    table_found = True
                    break
        assert table_found, "Table should be printed for list"

    @pytest.mark.asyncio
    async def test_stager_stop_no_id(self, sliver_command, mock_console):
        """Test stager stop without listener ID."""
        await sliver_command.handle_stager(["stop"])

        printed_content = str(mock_console.print.call_args_list)
        assert "Usage: /sliver stager stop <listener-id>" in printed_content

    @pytest.mark.asyncio
    async def test_stager_stop_success(self, sliver_command, mock_c2, mock_console):
        """Test successful stager stop."""
        mock_c2.stop_stager_listener = AsyncMock(return_value=True)

        await sliver_command.handle_stager(["stop", "stg-test123"])

        mock_c2.stop_stager_listener.assert_called_once_with("stg-test123")
        printed_content = str(mock_console.print.call_args_list)
        assert "Stopped stager listener: stg-test123" in printed_content

    @pytest.mark.asyncio
    async def test_stager_create_no_args(self, sliver_command, mock_console):
        """Test stager create without required arguments."""
        await sliver_command.handle_stager(["create"])

        printed_content = str(mock_console.print.call_args_list)
        assert "Usage: /sliver stager create <listener-id> --type <type>" in printed_content

    @pytest.mark.asyncio
    async def test_stager_create_invalid_type(self, sliver_command, mock_console):
        """Test stager create with invalid type."""
        await sliver_command.handle_stager(["create", "stg-test123", "--type", "invalid"])

        printed_content = str(mock_console.print.call_args_list)
        assert "Invalid stager type: invalid" in printed_content
        assert "Valid types: python, python2, python3, bash, powershell, vbs, minimal, debug" in printed_content

    @pytest.mark.asyncio
    async def test_stager_create_success(self, sliver_command, mock_c2, mock_console):
        """Test successful stager create."""
        listener = StagerListener(
            id="stg-test123",
            name="default",
            url="http://10.10.14.2:54321",
            host="10.10.14.2",
            port=54321,
            protocol="http",
            status="running",
            started_at=datetime.now(),
        )
        mock_c2.list_stager_listeners = AsyncMock(return_value=[listener])

        await sliver_command.handle_stager(["create", "stg-test123", "--type", "bash"])

        printed_content = str(mock_console.print.call_args_list)
        assert "Bash Stager:" in printed_content
        assert "curl -s" in printed_content
        assert "http://10.10.14.2:54321/s" in printed_content

    @pytest.mark.asyncio
    async def test_stager_create_listener_not_found(self, sliver_command, mock_c2, mock_console):
        """Test stager create with non-existent listener."""
        mock_c2.list_stager_listeners = AsyncMock(return_value=[])

        await sliver_command.handle_stager(["create", "stg-nonexistent", "--type", "python"])

        printed_content = str(mock_console.print.call_args_list)
        assert "Stager listener 'stg-nonexistent' not found" in printed_content

    @pytest.mark.asyncio
    async def test_stager_unknown_subcommand(self, sliver_command, mock_console):
        """Test unknown stager subcommand."""
        await sliver_command.handle_stager(["unknown"])

        # Check error message and help panel
        all_printed = []
        for call in mock_console.print.call_args_list:
            if call[0]:
                all_printed.append(str(call[0][0]))
        full_output = "\n".join(all_printed)

        assert "Unknown stager command: unknown" in full_output

        # Help panel should also be shown
        panel_found = False
        for call in mock_console.print.call_args_list:
            if len(call[0]) > 0 and hasattr(call[0][0], "__class__"):
                if call[0][0].__class__.__name__ == "Panel":
                    panel_found = True
                    break
        assert panel_found, "Help panel should be shown for unknown command"

    @pytest.mark.asyncio
    async def test_stager_create_minimal_type(self, sliver_command, mock_c2, mock_console):
        """Test stager create with minimal type."""
        listener = StagerListener(
            id="stg-test123",
            name="default",
            url="http://10.10.14.2:54321",
            host="10.10.14.2",
            port=54321,
            protocol="http",
            status="running",
            started_at=datetime.now(),
        )
        mock_c2.list_stager_listeners = AsyncMock(return_value=[listener])

        await sliver_command.handle_stager(["create", "stg-test123", "--type", "minimal"])

        printed_content = str(mock_console.print.call_args_list)
        assert "Minimal Stager:" in printed_content
        assert "import urllib2;exec(urllib2.urlopen(" in printed_content
        assert "Note: Minimal stager assumes Linux 32-bit" in printed_content

    @pytest.mark.asyncio
    async def test_stager_create_debug_type(self, sliver_command, mock_c2, mock_console):
        """Test stager create with debug type."""
        listener = StagerListener(
            id="stg-test123",
            name="default",
            url="http://10.10.14.2:54321",
            host="10.10.14.2",
            port=54321,
            protocol="http",
            status="running",
            started_at=datetime.now(),
        )
        mock_c2.list_stager_listeners = AsyncMock(return_value=[listener])

        await sliver_command.handle_stager(["create", "stg-test123", "--type", "debug"])

        printed_content = str(mock_console.print.call_args_list)
        assert "Debug Stager:" in printed_content
        assert "[DEBUG]" in printed_content
        assert "Note: Debug stager outputs verbose info to stderr" in printed_content


class TestNotConnectedHandling:
    """Test behavior when not connected to C2."""

    @pytest.mark.asyncio
    async def test_stager_start_not_connected(self, sliver_command, mock_c2, mock_console):
        """Test stager start when not connected."""
        mock_c2.is_connected = AsyncMock(return_value=False)

        await sliver_command.handle_stager(["start", "--host", "10.10.14.2"])

        printed_content = str(mock_console.print.call_args_list)
        assert "Not connected to Sliver C2 server" in printed_content

    @pytest.mark.asyncio
    async def test_stager_list_not_connected(self, sliver_command, mock_c2, mock_console):
        """Test stager list when not connected."""
        mock_c2.is_connected = AsyncMock(return_value=False)

        await sliver_command.handle_stager(["list"])

        printed_content = str(mock_console.print.call_args_list)
        assert "Not connected to Sliver C2 server" in printed_content
