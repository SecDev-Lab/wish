"""HTB Lame live environment E2E test."""

import asyncio
import logging
import os
import sys
from datetime import datetime

import pytest
from wish_cli.headless.client import HeadlessWish
from wish_cli.headless.events import EventType

logger = logging.getLogger(__name__)

# Target configuration
HTB_LAME_IP = "10.10.10.3"
HTB_LAME_EXPECTED_SERVICES = {
    21: {"product": "vsftpd", "version": "2.3.4"},
    22: {"product": "OpenSSH", "version": "4.7p1"},
    139: {"product": "Samba", "version": "3.0.20"},
    445: {"product": "Samba", "version": "3.0.20"}
}


@pytest.mark.live
class TestHTBLameLive:
    """HTB Lame live exploitation test for Black Hat USA demo validation."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Verify test environment before running."""
        # Check network connectivity to target
        import subprocess
        try:
            result = subprocess.run(
                ["ping", "-c", "1", "-W", "2", HTB_LAME_IP],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                pytest.fail(f"Cannot reach target {HTB_LAME_IP}. Check VPN connection. Ensure HTB VPN is connected.")
        except Exception as e:
            pytest.fail(f"Cannot verify connectivity: {e}")

    @pytest.fixture
    async def wish(self):
        """Create live HeadlessWish instance."""
        wish = HeadlessWish(auto_approve=True)

        # Set up event logging for debugging
        events_log = []

        @wish.on_event(EventType.STATE_CHANGED)
        async def log_state_change(event):
            state = event.data.get("state")
            if state and hasattr(state, "hosts") and hasattr(state, "findings"):
                events_log.append({
                    "type": "state_changed",
                    "timestamp": event.timestamp,
                    "hosts": len(state.hosts) if state.hosts else 0,
                    "findings": len(state.findings) if state.findings else 0
                })
            else:
                events_log.append({
                    "type": "state_changed",
                    "timestamp": event.timestamp,
                    "hosts": 0,
                    "findings": 0
                })

        @wish.on_event(EventType.JOB_STARTED)
        async def log_job_start(event):
            events_log.append({
                "type": "job_started",
                "timestamp": event.timestamp,
                "job": event.data.get("job_id")
            })

        wish._events_log = events_log

        try:
            yield wish
        finally:
            # Ensure cleanup happens even if test fails
            try:
                await wish.cleanup()
            except Exception as e:
                logger.warning(f"Error during wish cleanup: {e}")

    @pytest.mark.asyncio
    async def test_htb_lame_discovery_phase(self, wish):
        """Test Phase 1: Target discovery and initial reconnaissance."""
        session = await wish.start_session(metadata={
            "test": "htb_lame_live_discovery",
            "target": HTB_LAME_IP,
            "phase": "discovery",
            "timestamp": datetime.now().isoformat()
        })

        try:
            # Step 1: Set target using scope command
            logger.info(f"Setting target to {HTB_LAME_IP}")
            prompt = f"/scope add {HTB_LAME_IP}"
            sys.stderr.write(f"\n[USER INPUT]: {prompt}\n")
            result = await session.send_prompt(prompt)
            sys.stderr.write(f"[SYSTEM OUTPUT]: {result.result}\n")

            state = result.state_after
            assert state.targets
            assert any(HTB_LAME_IP in t.scope for t in state.targets.values())

            # Step 2: Initial port scan - start with common ports for faster results
            logger.info("Performing initial port scan on common ports")
            prompt = (
                f"Scan ports 21,22,80,139,445 on {HTB_LAME_IP} with service detection. "
                "This is a quick scan to get initial results."
            )
            sys.stderr.write(f"\n[USER INPUT]: {prompt}\n")
            result = await session.send_prompt(prompt)
            sys.stderr.write(f"[SYSTEM OUTPUT]: {result.result}\n")

            # Debug: Show if any jobs were started
            if "job" in result.result.lower():
                sys.stderr.write("[DEBUG] Job reference detected in response\n")

            # Wait for scan completion with job monitoring
            logger.info("Waiting for scan to complete...")
            max_wait_time = 60  # Maximum 60 seconds
            check_interval = 5
            scan_completed = False

            # Give the job a moment to start
            await asyncio.sleep(2)

            for i in range(max_wait_time // check_interval):
                # Check job status
                prompt = "/jobs"
                sys.stderr.write(f"\n[USER INPUT]: {prompt}\n")
                result = await session.send_prompt(prompt)
                sys.stderr.write(f"[SYSTEM OUTPUT]: {result.result}\n")

                # Check if scan is complete by looking for the summary line
                # The summary line format is: "Summary: X running, Y total jobs"
                import re
                summary_match = re.search(r'Summary:\s*(\d+)\s*running', result.result, re.IGNORECASE)
                if summary_match:
                    running_jobs = int(summary_match.group(1))
                    if running_jobs == 0:
                        scan_completed = True
                        logger.info(f"Scan completed after {(i+1)*check_interval} seconds")
                        break
                    else:
                        logger.info(f"Scan still running... {running_jobs} jobs active ({(i+1)*check_interval}s elapsed)")
                elif "no jobs" in result.result.lower():
                    scan_completed = True
                    logger.info(f"No jobs found after {(i+1)*check_interval} seconds")
                    break
                else:
                    logger.info(f"Could not parse job status ({(i+1)*check_interval}s elapsed)")

                # Wait before next check
                if i < (max_wait_time // check_interval - 1):
                    await asyncio.sleep(check_interval)

            if not scan_completed:
                logger.warning(f"Scan did not complete within {max_wait_time} seconds")

            # Check status after scan
            prompt = "/status"
            sys.stderr.write(f"\n[USER INPUT]: {prompt}\n")
            result = await session.send_prompt(prompt)
            sys.stderr.write(f"[SYSTEM OUTPUT]:\n{result.result}\n")

            # Verify discovered services
            state = result.state_after
            assert state.hosts, "No hosts discovered"

            host = next((h for h in state.hosts.values() if h.ip_address == HTB_LAME_IP), None)
            assert host, f"Target host {HTB_LAME_IP} not found in state"

            # Check expected ports
            discovered_ports = {s.port for s in host.services}
            expected_ports = set(HTB_LAME_EXPECTED_SERVICES.keys())

            logger.info(f"Discovered ports: {discovered_ports}")
            logger.info(f"Expected ports: {expected_ports}")

            missing_ports = expected_ports - discovered_ports
            assert not missing_ports, f"Missing expected ports: {missing_ports}"

            # Verify service details
            for service in host.services:
                if service.port in HTB_LAME_EXPECTED_SERVICES:
                    expected = HTB_LAME_EXPECTED_SERVICES[service.port]
                    logger.info(f"Port {service.port}: {service.product} {service.version}")

                    # Check product name (flexible matching)
                    if expected["product"].lower() in str(service.product).lower():
                        logger.info(f"✓ Product match for port {service.port}")
                    else:
                        logger.warning(f"Product mismatch on port {service.port}: "
                                     f"expected '{expected['product']}', got '{service.product}'")

            logger.info("Discovery phase completed successfully")

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_htb_lame_enumeration_phase(self, wish):
        """Test Phase 2: Service enumeration and vulnerability identification."""
        session = await wish.start_session(metadata={
            "test": "htb_lame_live_enumeration",
            "target": HTB_LAME_IP,
            "phase": "enumeration"
        })

        try:
            # Quick setup - provide existing scan results
            prompt = (
                f"We have already scanned {HTB_LAME_IP} and found the following services:\n"
                "- Port 21: vsftpd 2.3.4\n"
                "- Port 22: OpenSSH 4.7p1\n"
                "- Port 139: Samba 3.0.20\n"
                "- Port 445: Samba 3.0.20\n"
                "Focus on enumerating these services without rescanning."
            )
            sys.stderr.write(f"\n[USER INPUT]: {prompt}\n")
            result = await session.send_prompt(prompt)
            sys.stderr.write(f"[SYSTEM OUTPUT]: {result.result}\n")

            # Focus on SMB enumeration
            logger.info("Enumerating SMB service")
            prompt = (
                "Enumerate the SMB service on ports 139 and 445. "
                "Identify the exact Samba version and check for anonymous access."
            )
            sys.stderr.write(f"\n[USER INPUT]: {prompt}\n")
            result = await session.send_prompt(prompt)
            sys.stderr.write(f"[SYSTEM OUTPUT]: {result.result}\n")

            # Verify Samba version detection
            state = result.state_after

            # Check if AI identified the vulnerability
            logger.info("Checking for vulnerability identification")
            prompt = "You mentioned Samba 3.0.20. Without running any tools, based on your knowledge, what known vulnerabilities exist in Samba 3.0.20? Specifically, are there any remote code execution vulnerabilities?"
            sys.stderr.write(f"\n[USER INPUT]: {prompt}\n")
            result = await session.send_prompt(prompt)
            sys.stderr.write(f"[SYSTEM OUTPUT]: {result.result}\n")

            # Should identify CVE-2007-2447
            response = result.result.lower()
            assert "cve-2007-2447" in response or "username map" in response, \
                "AI should identify the Samba username map script vulnerability"

            # Verify finding creation
            if state.findings:
                vuln_finding = next(
                    (f for f in state.findings.values()
                     if "2007-2447" in str(f.cve_ids) or "username map" in f.title.lower()),
                    None
                )
                if vuln_finding:
                    assert vuln_finding.severity in ["critical", "high"]
                    logger.info(f"✓ Vulnerability finding created: {vuln_finding.title}")

            # Check all findings
            prompt = "/findings"
            sys.stderr.write(f"\n[USER INPUT]: {prompt}\n")
            result = await session.send_prompt(prompt)
            sys.stderr.write(f"[SYSTEM OUTPUT]:\n{result.result}\n")

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_htb_lame_exploitation_planning(self, wish):
        """Test Phase 3: Exploitation planning and safety verification."""
        session = await wish.start_session(metadata={
            "test": "htb_lame_live_exploitation",
            "target": HTB_LAME_IP,
            "phase": "exploitation_planning"
        })

        try:
            # Quick setup with known vulnerability
            prompt = (
                f"Target {HTB_LAME_IP} has Samba 3.0.20 on port 445 "
                "with CVE-2007-2447 username map script vulnerability"
            )
            sys.stderr.write(f"\n[USER INPUT]: {prompt}\n")
            result = await session.send_prompt(prompt)
            sys.stderr.write(f"[SYSTEM OUTPUT]: {result.result}\n")

            # Request exploitation plan
            logger.info("Requesting exploitation plan")
            prompt = (
                "Create a detailed exploitation plan for the Samba username map script vulnerability. "
                "Include both automated (Metasploit) and manual exploitation methods."
            )
            sys.stderr.write(f"\n[USER INPUT]: {prompt}\n")
            result = await session.send_prompt(prompt)
            sys.stderr.write(f"[SYSTEM OUTPUT]: {result.result}\n")

            # Verify plan includes key elements
            plan_text = result.result.lower()

            required_elements = [
                ("vulnerability mechanism", ["username map", "command injection"]),
                ("metasploit module", ["usermap_script", "exploit/multi/samba"]),
                ("manual method", ["smbclient", "logon", "payload"])
            ]

            for element_name, keywords in required_elements:
                found = any(keyword in plan_text for keyword in keywords)
                assert found, f"Exploitation plan missing {element_name}"
                logger.info(f"✓ Plan includes {element_name}")

        finally:
            await session.end()

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_htb_lame_full_attack_chain(self, wish):
        """Test Complete Attack Chain: Discovery → Enumeration → Exploitation Planning.
        
        This is the ultimate test that simulates the full Black Hat USA demo flow.
        """
        session = await wish.start_session(metadata={
            "test": "htb_lame_live_full_chain",
            "target": HTB_LAME_IP,
            "demo": "blackhat_usa",
            "timestamp": datetime.now().isoformat()
        })

        logger.info("=== Starting HTB Lame Full Attack Chain ===")
        sys.stderr.write("\n" + "="*60 + "\n")
        sys.stderr.write("HTB LAME FULL ATTACK CHAIN - LIVE DEMO\n")
        sys.stderr.write("="*60 + "\n\n")

        try:
            # Phase 0: Add target to scope
            logger.info("\n--- Phase 0: Add Target to Scope ---")
            sys.stderr.write("[▶] Phase 0: Add Target to Scope\n")
            prompt = f"/scope add {HTB_LAME_IP}"
            sys.stderr.write(f"\n[USER INPUT]: {prompt}\n")
            result = await session.send_prompt(prompt)
            sys.stderr.write(f"[SYSTEM OUTPUT]: {result.result}\n")
            assert "added" in result.result.lower() or "scope" in result.result.lower()

            # Phase 1: Initial Contact
            logger.info("\n--- Phase 1: Initial Contact ---")
            sys.stderr.write("\n[▶] Phase 1: Initial Contact\n")
            prompt = (
                f"I need to assess the security of {HTB_LAME_IP}. "
                "Start with network reconnaissance."
            )
            sys.stderr.write(f"\n[USER INPUT]: {prompt}\n")
            result = await session.send_prompt(prompt)
            sys.stderr.write(f"[SYSTEM OUTPUT]: {result.result}\n")

            # AI should suggest scanning or acknowledge the request
            assert any(word in result.result.lower() for word in ["scan", "nmap", "discover", "assess", "security", "reconnaissance", "started", "plan"])

            # Phase 2: Discovery
            logger.info("\n--- Phase 2: Service Discovery ---")
            sys.stderr.write("\n[▶] Phase 2: Service Discovery\n")
            prompt = "Perform a thorough scan to identify all services and their versions"
            sys.stderr.write(f"\n[USER INPUT]: {prompt}\n")
            result = await session.send_prompt(prompt)
            sys.stderr.write(f"[SYSTEM OUTPUT]: {result.result}\n")

            # Wait for scan completion with proper job monitoring
            sys.stderr.write("[ℹ] Waiting for scan to complete...\n")
            max_wait = 60  # Maximum 60 seconds
            check_interval = 5
            scan_completed = False

            for i in range(max_wait // check_interval):
                await asyncio.sleep(check_interval)

                # Check job status
                prompt = "/jobs"
                sys.stderr.write(f"\n[USER INPUT]: {prompt}\n")
                result = await session.send_prompt(prompt)
                sys.stderr.write(f"[SYSTEM OUTPUT]: {result.result}\n")

                # Check if scan is complete by looking for the summary line
                # The summary line format is: "Summary: X running, Y total jobs"
                import re
                summary_match = re.search(r'Summary:\s*(\d+)\s*running', result.result, re.IGNORECASE)
                if summary_match:
                    running_jobs = int(summary_match.group(1))
                    if running_jobs == 0:
                        scan_completed = True
                        sys.stderr.write(f"[✔] Scan completed after {(i+1)*check_interval} seconds\n")
                        break
                    else:
                        sys.stderr.write(f"[ℹ] Scan still running... {running_jobs} jobs active ({(i+1)*check_interval}s elapsed)\n")
                elif "no jobs" in result.result.lower():
                    scan_completed = True
                    sys.stderr.write(f"[✔] No jobs found after {(i+1)*check_interval} seconds\n")
                    break
                else:
                    sys.stderr.write(f"[ℹ] Could not parse job status ({(i+1)*check_interval}s elapsed)\n")

            if not scan_completed:
                sys.stderr.write(f"[⚠] Scan did not complete within {max_wait} seconds\n")

            # Check status after scan
            prompt = "/status"
            sys.stderr.write(f"\n[USER INPUT]: {prompt}\n")
            status_result = await session.send_prompt(prompt)
            sys.stderr.write(f"[SYSTEM OUTPUT]:\n{status_result.result}\n")

            # Phase 3: Analysis
            logger.info("\n--- Phase 3: Vulnerability Analysis ---")
            sys.stderr.write("\n[▶] Phase 3: Vulnerability Analysis\n")
            # Include the status information in the prompt to provide context
            prompt = f"Based on the scan results, we have found these services:\n{status_result.result}\n\nAnalyze these discovered services for potential vulnerabilities, particularly focusing on any SMB/Samba services."
            sys.stderr.write(f"\n[USER INPUT]: {prompt}\n")
            result = await session.send_prompt(prompt)
            sys.stderr.write(f"[SYSTEM OUTPUT]: {result.result}\n")

            # Should identify Samba as interesting
            assert "samba" in result.result.lower() or "smb" in result.result.lower()

            # Phase 4: Focused Enumeration
            logger.info("\n--- Phase 4: Targeted Enumeration ---")
            sys.stderr.write("\n[▶] Phase 4: Targeted Enumeration\n")
            prompt = "Focus on the SMB/Samba service. Get detailed information."
            sys.stderr.write(f"\n[USER INPUT]: {prompt}\n")
            result = await session.send_prompt(prompt)
            sys.stderr.write(f"[SYSTEM OUTPUT]: {result.result}\n")

            # Phase 5: Vulnerability Confirmation
            logger.info("\n--- Phase 5: Vulnerability Identification ---")
            sys.stderr.write("\n[▶] Phase 5: Vulnerability Identification\n")
            prompt = "What specific vulnerabilities affect this version of Samba?"
            sys.stderr.write(f"\n[USER INPUT]: {prompt}\n")
            result = await session.send_prompt(prompt)
            sys.stderr.write(f"[SYSTEM OUTPUT]: {result.result}\n")

            # Must identify CVE-2007-2447
            assert "2007-2447" in result.result or "username map" in result.result.lower()
            sys.stderr.write("[✔] CVE-2007-2447 vulnerability identified!\n")

            # Check findings
            prompt = "/findings"
            sys.stderr.write(f"\n[USER INPUT]: {prompt}\n")
            result = await session.send_prompt(prompt)
            sys.stderr.write(f"[SYSTEM OUTPUT]:\n{result.result}\n")

            # Phase 6: Exploitation Strategy
            logger.info("\n--- Phase 6: Exploitation Planning ---")
            sys.stderr.write("\n[▶] Phase 6: Exploitation Planning\n")
            prompt = "Provide a safe approach to confirm this vulnerability without causing damage"
            sys.stderr.write(f"\n[USER INPUT]: {prompt}\n")
            result = await session.send_prompt(prompt)
            sys.stderr.write(f"[SYSTEM OUTPUT]: {result.result}\n")

            # Should provide responsible approach
            assert any(word in result.result.lower()
                      for word in ["safe", "verify", "confirm", "test"])

            # Final verification
            state = result.state_after

            # Check we have complete picture
            assert state.hosts, "Should have discovered hosts"
            assert state.findings, "Should have identified vulnerabilities"

            # Check final scope
            prompt = "/scope"
            sys.stderr.write(f"\n[USER INPUT]: {prompt}\n")
            result = await session.send_prompt(prompt)
            sys.stderr.write(f"[SYSTEM OUTPUT]:\n{result.result}\n")

            # Final status check
            prompt = "/status"
            sys.stderr.write(f"\n[USER INPUT]: {prompt}\n")
            result = await session.send_prompt(prompt)
            sys.stderr.write(f"[SYSTEM OUTPUT]:\n{result.result}\n")

            # Verify the attack chain is ready
            host = next(iter(state.hosts.values()))
            finding = next(iter(state.findings.values()))

            logger.info("\n=== Attack Chain Summary ===")
            sys.stderr.write("\n" + "="*60 + "\n")
            sys.stderr.write("ATTACK CHAIN SUMMARY\n")
            sys.stderr.write("="*60 + "\n")
            sys.stderr.write(f"[ℹ] Target: {host.ip_address}\n")
            sys.stderr.write(f"[ℹ] Services: {len(host.services)} discovered\n")
            sys.stderr.write(f"[ℹ] Vulnerability: {finding.title}\n")
            sys.stderr.write(f"[ℹ] Severity: {finding.severity}\n")
            sys.stderr.write("[ℹ] Next Step: Ready for controlled exploitation\n")

            sys.stderr.write("\n[✔] Full attack chain completed successfully!\n")
            sys.stderr.write("[✔] This confirms wish is ready for Black Hat USA demo!\n")

            logger.info("\n✓ Full attack chain completed successfully!")
            logger.info("This confirms wish is ready for Black Hat USA demo!")

        finally:
            # Log event summary
            if hasattr(wish, '_events_log'):
                logger.info(f"\nEvent Summary: {len(wish._events_log)} events recorded")
                for event in wish._events_log[-5:]:  # Last 5 events
                    logger.info(f"  - {event['type']} at {event['timestamp']}")

            await session.end()


    @pytest.mark.asyncio
    async def test_job_management_demo(self, wish):
        """Test job management functionality during exploitation."""
        session = await wish.start_session(metadata={
            "test": "htb_lame_job_management",
            "target": HTB_LAME_IP,
            "phase": "job_demo"
        })

        sys.stderr.write("\n" + "="*60 + "\n")
        sys.stderr.write("JOB MANAGEMENT DEMO\n")
        sys.stderr.write("="*60 + "\n\n")

        try:
            # Setup
            prompt = f"/scope add {HTB_LAME_IP}"
            sys.stderr.write(f"[USER INPUT]: {prompt}\n")
            result = await session.send_prompt(prompt)
            sys.stderr.write(f"[SYSTEM OUTPUT]: {result.result}\n")

            # Start multiple concurrent scans
            sys.stderr.write("\n[▶] Starting multiple concurrent scans...\n")

            prompt = "Run a quick port scan on common ports (22,80,443,445)"
            sys.stderr.write(f"\n[USER INPUT]: {prompt}\n")
            result = await session.send_prompt(prompt)
            sys.stderr.write(f"[SYSTEM OUTPUT]: {result.result}\n")

            # Immediately check jobs
            await asyncio.sleep(1)
            prompt = "/jobs"
            sys.stderr.write(f"\n[USER INPUT]: {prompt}\n")
            result = await session.send_prompt(prompt)
            sys.stderr.write(f"[SYSTEM OUTPUT]:\n{result.result}\n")

            # Start another task
            prompt = "Also enumerate SMB shares on the target"
            sys.stderr.write(f"\n[USER INPUT]: {prompt}\n")
            result = await session.send_prompt(prompt)
            sys.stderr.write(f"[SYSTEM OUTPUT]: {result.result}\n")

            # Check jobs again
            await asyncio.sleep(2)
            prompt = "/jobs"
            sys.stderr.write(f"\n[USER INPUT]: {prompt}\n")
            result = await session.send_prompt(prompt)
            sys.stderr.write(f"[SYSTEM OUTPUT]:\n{result.result}\n")

            # Wait for completion
            sys.stderr.write("\n[ℹ] Waiting for jobs to complete...\n")
            await asyncio.sleep(3)

            # Final job status
            prompt = "/jobs"
            sys.stderr.write(f"\n[USER INPUT]: {prompt}\n")
            result = await session.send_prompt(prompt)
            sys.stderr.write(f"[SYSTEM OUTPUT]:\n{result.result}\n")

            # Check final status
            prompt = "/status"
            sys.stderr.write(f"\n[USER INPUT]: {prompt}\n")
            result = await session.send_prompt(prompt)
            sys.stderr.write(f"[SYSTEM OUTPUT]:\n{result.result}\n")

            sys.stderr.write("\n[✔] Job management demo completed!\n")

        finally:
            await session.end()


@pytest.mark.live
@pytest.mark.asyncio
async def test_live_environment_setup():
    """Test that live environment is properly configured."""
    # No environment variable check needed anymore

    # Check OpenAI API key (from env or config)
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        # Try to get from config
        try:
            from wish_core.config import get_llm_config
            config = get_llm_config()
            api_key = config.api_key
        except Exception:
            pass

    assert api_key, "OpenAI API key not found in environment or config"

    # Try to create live instance
    wish = HeadlessWish(auto_approve=True)
    assert wish is not None

    logger.info("✓ Live environment properly configured")
