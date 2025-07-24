"""HTB Lame scenario E2E test using HeadlessWish."""

import os
import sys

import pytest
from wish_cli.headless import EventType, HeadlessWish

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from fixtures import HTB_LAME_SCENARIO, MockEventCollector, setup_mocks


class TestHTBLameScenario:
    """Complete HTB Lame penetration test scenario."""

    @pytest.mark.asyncio
    async def test_htb_lame_full_scenario(self):
        """HTB Lame scenario: discovery → enumeration → exploitation."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        # Track scenario progress
        collector = MockEventCollector()
        scenario_events = []

        @wish.on_event(EventType.STATE_CHANGED)
        async def on_state_change(event):
            scenario_events.append({
                "type": "state_change",
                "timestamp": event.timestamp,
                "data": event.data
            })

        @wish.on_event(EventType.JOB_COMPLETED)
        async def on_job_complete(event):
            scenario_events.append({
                "type": "job_complete",
                "timestamp": event.timestamp,
                "data": event.data
            })

        session = await wish.start_session(metadata={
            "scenario": "htb_lame",
            "target": HTB_LAME_SCENARIO["target"]
        })

        try:
            # ACT 1: Initial Reconnaissance

            # Set target
            result = await session.send_prompt(f"set target {HTB_LAME_SCENARIO['target']}")
            assert len(result.state_after.targets) == 1

            # Initial scan
            result = await session.send_prompt("perform initial port scan")
            state = await session.get_state()

            # Verify host discovered
            assert len(state.hosts) > 0
            lame_host = next((h for h in state.hosts.values()
                             if h.ip_address == HTB_LAME_SCENARIO["target"]), None)
            assert lame_host is not None

            # Verify expected services
            discovered_ports = {s.port for s in lame_host.services}
            expected_ports = {s["port"] for s in HTB_LAME_SCENARIO["expected_services"]}
            assert expected_ports.issubset(discovered_ports)


            # ACT 2: Service Enumeration

            # Enumerate SMB
            result = await session.send_prompt("enumerate the SMB service in detail")

            # Check for Samba version detection
            state = await session.get_state()
            samba_service = next((s for s in lame_host.services if s.port == 445), None)
            assert samba_service is not None
            assert samba_service.product is not None
            assert "samba" in samba_service.product.lower()


            # ACT 3: Vulnerability Analysis

            # Check for vulnerabilities
            result = await session.send_prompt("check if the Samba version is vulnerable")

            # Should identify CVE-2007-2447
            state = await session.get_state()
            assert len(state.findings) > 0

            # Find the Samba vulnerability
            samba_vuln = next((f for f in state.findings.values()
                              if HTB_LAME_SCENARIO["vulnerability"] in str(f.cve_ids)), None)
            assert samba_vuln is not None
            assert samba_vuln.severity == "critical"


            # ACT 4: Exploitation

            # Attempt exploitation
            result = await session.send_prompt("exploit the Samba username map script vulnerability")

            # Check exploitation success (in mock)
            assert "successful" in result.result.lower() or "shell" in result.result.lower()

            # Verify privilege level
            result = await session.send_prompt("check current privileges")
            assert HTB_LAME_SCENARIO["expected_privs"] in result.result.lower()


            # ACT 5: Post-Exploitation

            # Basic post-exploitation
            result = await session.send_prompt("what post-exploitation steps should I take?")

            # Should suggest various post-exploitation activities
            suggestions_lower = result.result.lower()
            assert any(activity in suggestions_lower for activity in
                      ["persistence", "escalate", "lateral", "exfiltrate", "clean"])

            # Summary
            summary = await session.end()

            # Verify complete scenario execution
            assert summary.prompts_executed >= 7  # All major steps
            assert summary.hosts_discovered >= 1
            assert summary.findings >= 1

        except Exception:
            raise

    @pytest.mark.asyncio
    async def test_htb_lame_alternative_paths(self):
        """Test alternative exploitation paths for HTB Lame."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        session = await wish.start_session(metadata={"scenario": "htb_lame_alt"})

        try:
            # Quick setup
            await session.send_prompt(f"scan {HTB_LAME_SCENARIO['target']}")

            # Try distcc exploitation path
            result = await session.send_prompt("check if distcc service on port 3632 is exploitable")

            # AI should recognize distcc as potentially vulnerable
            assert "distcc" in result.result.lower()

            # Try FTP path
            result = await session.send_prompt("check the FTP service for vulnerabilities")

            # Should mention vsftpd version
            assert "vsftpd" in result.result.lower() or "ftp" in result.result.lower()

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_htb_lame_defensive_recommendations(self):
        """Test defensive recommendations after compromise."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        session = await wish.start_session()

        try:
            # Quick compromise setup
            await session.send_prompt(f"assume we've compromised {HTB_LAME_SCENARIO['target']} via Samba")

            # Ask for defensive recommendations
            result = await session.send_prompt("what defensive measures would prevent this attack?")

            # Should provide relevant security recommendations
            recommendations = result.result.lower()

            expected_defenses = [
                "patch",
                "update",
                "firewall",
                "disable",
                "harden",
                "monitor",
                "segment"
            ]

            found_defenses = [d for d in expected_defenses if d in recommendations]
            assert len(found_defenses) >= 3, f"Expected defensive recommendations, found: {found_defenses}"

            # Ask for specific Samba hardening
            result = await session.send_prompt("how specifically to harden Samba against this attack?")

            # Should mention specific configurations
            assert any(config in result.result.lower() for config in
                      ["username map", "map script", "smb.conf", "disable"])

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_htb_lame_learning_mode(self):
        """Test educational aspects of the scenario."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        session = await wish.start_session(metadata={"mode": "learning"})

        try:
            # Educational questions about the target
            result = await session.send_prompt(f"explain why {HTB_LAME_SCENARIO['target']} is called 'Lame'")

            # Should provide educational context
            assert len(result.result) > 50  # Non-trivial explanation

            # Ask about the vulnerability
            result = await session.send_prompt(f"explain how {HTB_LAME_SCENARIO['vulnerability']} works")

            # Should explain the vulnerability
            explanation = result.result.lower()
            assert any(concept in explanation for concept in
                      ["injection", "command", "username", "map", "script"])

            # Ask for similar vulnerabilities
            result = await session.send_prompt("what are similar vulnerabilities to this one?")

            # Should mention related vulnerabilities
            assert any(vuln_type in result.result.lower() for vuln_type in
                      ["injection", "rce", "command execution"])

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_htb_lame_scenario_variations(self):
        """Test scenario with variations and constraints."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        # Test 1: Stealth mode
        session = await wish.start_session(metadata={"mode": "stealth"})

        try:
            result = await session.send_prompt(f"scan {HTB_LAME_SCENARIO['target']} stealthily")

            # Should suggest stealthy techniques
            assert any(stealth in result.result.lower() for stealth in
                      ["syn", "stealth", "ids", "evasion", "slow"])

        finally:
            await session.end()

        # Test 2: Limited tools
        session = await wish.start_session(metadata={"constraints": "no-automated-exploits"})

        try:
            await session.send_prompt(f"scan {HTB_LAME_SCENARIO['target']}")
            result = await session.send_prompt("exploit Samba manually without metasploit")

            # Should provide manual exploitation guidance
            assert any(manual in result.result.lower() for manual in
                      ["manual", "python", "netcat", "telnet", "custom"])

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_htb_lame_reporting(self):
        """Test report generation for the scenario."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        session = await wish.start_session()

        try:
            # Run abbreviated scenario
            await session.send_prompt(f"scan {HTB_LAME_SCENARIO['target']}")
            await session.send_prompt("find and exploit the Samba vulnerability")

            # Request report
            result = await session.send_prompt("generate a penetration test report summary")

            report = result.result.lower()

            # Report should contain key sections
            report_sections = [
                "executive summary",
                "finding",
                "impact",
                "recommendation",
                "evidence"
            ]

            # At least some sections should be present
            found_sections = [s for s in report_sections if s in report]
            assert len(found_sections) >= 2, f"Expected report sections, found: {found_sections}"

            # Should mention the specific vulnerability
            assert HTB_LAME_SCENARIO["vulnerability"] in result.result or "samba" in report

        finally:
            await session.end()
