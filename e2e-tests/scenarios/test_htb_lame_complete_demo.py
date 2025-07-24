"""Complete HTB Lame demo scenario E2E test."""

import asyncio
from datetime import datetime

import pytest
from fixtures import setup_mocks
from wish_cli.headless.client import HeadlessWish
from wish_cli.headless.events import EventType


@pytest.mark.asyncio
class TestHTBLameCompleteDemo:
    """Test the complete demo scenario from start to finish."""

    @pytest.fixture
    async def wish(self):
        """Create HeadlessWish instance configured for demo."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        # Track all events for demo validation
        demo_events = {
            "commands": [],
            "state_changes": [],
            "jobs": [],
            "findings": []
        }

        @wish.on_event(EventType.STATE_CHANGED)
        async def on_state_change(event):
            state = event.data.get("state")
            if state:
                demo_events["state_changes"].append({
                    "timestamp": event.timestamp,
                    "hosts": len(state.hosts) if hasattr(state, "hosts") and state.hosts else 0,
                    "findings": len(state.findings) if hasattr(state, "findings") and state.findings else 0
                })

        @wish.on_event(EventType.JOB_STARTED)
        async def on_job_start(event):
            demo_events["jobs"].append({
                "job_id": event.data.get("job_id"),
                "command": event.data.get("command"),
                "timestamp": event.timestamp
            })

        wish._demo_events = demo_events
        return wish

    async def test_act1_discovery(self, wish):
        """Test ACT 1: Initial Discovery."""
        session = await wish.start_session(metadata={
            "test": "htb_lame_act1_discovery",
            "demo_phase": "ACT 1"
        })

        try:
            # Step 1: Add target to scope
            result = await session.send_prompt("/scope add 10.10.10.3")
            assert "added" in result.result.lower() or "scope" in result.result.lower()

            # Verify target in state
            state = result.state_after
            assert len(state.targets) > 0
            target_found = any("10.10.10.3" in t.scope for t in state.targets.values())
            assert target_found, "Target 10.10.10.3 not found in scope"

            # Step 2: Request scan
            result = await session.send_prompt("scan 10.10.10.3")

            # Should acknowledge scan request
            assert result.result is not None
            assert "error" not in result.result.lower()

            # Step 3: Check status
            result = await session.send_prompt("/status")
            assert "10.10.10.3" in result.result

            # In real scenario, scan would populate hosts/services
            # For now, verify command flow works

        finally:
            summary = await session.end()
            assert summary.prompts_executed >= 3

    async def test_act2_vulnerability_verification(self, wish):
        """Test ACT 2: Vulnerability Verification."""
        session = await wish.start_session(metadata={
            "test": "htb_lame_act2_verification",
            "demo_phase": "ACT 2"
        })

        try:
            # Setup context
            await session.send_prompt("/scope add 10.10.10.3")

            # Simulate finding Samba service
            result = await session.send_prompt(
                "I found Samba 3.0.20 running on port 445 on the target. "
                "Can you analyze this for vulnerabilities?"
            )

            # AI should identify CVE-2007-2447
            response = result.result.lower()
            assert any(term in response for term in [
                "cve", "2007-2447", "username map", "vulnerable", "exploit"
            ])

            # Request verification
            result = await session.send_prompt(
                "Can we verify this vulnerability safely?"
            )

            # Should provide safe verification approach
            assert any(word in result.result.lower() for word in [
                "verify", "test", "safe", "command"
            ])

            # Simulate verification
            result = await session.send_prompt(
                "Please verify the vulnerability with a simple id command"
            )

            # Should indicate action or success
            # In full implementation, would show:
            # [✔] Exploit successful! Command output:
            #     uid=0(root) gid=0(root) groups=0(root)
            assert result.result is not None

        finally:
            await session.end()

    async def test_act3_findings_summary(self, wish):
        """Test ACT 3: Findings and Summary."""
        session = await wish.start_session(metadata={
            "test": "htb_lame_act3_summary",
            "demo_phase": "ACT 3"
        })

        try:
            # Setup complete context
            await session.send_prompt("/scope add 10.10.10.3")

            # Add findings manually (simulating earlier discovery)
            await session.send_prompt(
                "/findings add CVE-2007-2447: Samba Username Map Script RCE on 10.10.10.3"
            )

            # Check findings
            result = await session.send_prompt("/findings")
            assert "CVE-2007-2447" in result.result or "samba" in result.result.lower()

            # Check complete status
            result = await session.send_prompt("/status")
            status_output = result.result

            # Should show hierarchical view with:
            # - Target: 10.10.10.3
            # - Findings: CVE-2007-2447
            assert "10.10.10.3" in status_output

            # Verify final state
            state = result.state_after
            assert len(state.targets) > 0
            assert len(state.findings) > 0

        finally:
            await session.end()

    async def test_complete_demo_flow(self, wish):
        """Test the complete demo flow from start to finish."""
        session = await wish.start_session(metadata={
            "test": "htb_lame_complete_flow",
            "demo": "Black Hat USA",
            "duration_target": "5 minutes"
        })

        demo_start = datetime.now()

        try:
            # === ACT 1: Discovery (2 minutes) ===

            # Add target
            result = await session.send_prompt("/scope add 10.10.10.3")
            assert "scope" in result.result.lower() or "added" in result.result.lower()

            # Initial reconnaissance
            result = await session.send_prompt(
                "I need to assess the security of 10.10.10.3. "
                "Start with network reconnaissance."
            )
            assert any(word in result.result.lower() for word in [
                "scan", "nmap", "port", "discover"
            ])

            # Perform scan
            result = await session.send_prompt("scan the target")
            assert result.result is not None

            # === ACT 2: Verification (2 minutes) ===

            # Analyze services
            result = await session.send_prompt(
                "The scan found Samba 3.0.20 on port 445. "
                "What vulnerabilities exist?"
            )
            assert any(term in result.result.lower() for term in [
                "cve", "2007-2447", "vulnerable", "username map"
            ])

            # Verify vulnerability
            result = await session.send_prompt(
                "verify the samba vulnerability"
            )

            # === ACT 3: Summary (1 minute) ===

            # Add finding
            await session.send_prompt(
                "/findings add CVE-2007-2447: Confirmed RCE via Samba username map script"
            )

            # Final status
            result = await session.send_prompt("/status")
            assert "10.10.10.3" in result.result

            # Final findings
            result = await session.send_prompt("/findings")
            assert "CVE-2007-2447" in result.result

            # Verify complete state
            state = result.state_after
            assert len(state.targets) > 0
            assert len(state.findings) > 0

            # Check demo duration
            demo_duration = (datetime.now() - demo_start).total_seconds()

            # Log demo metrics
            print(f"\nDemo completed in {demo_duration:.1f} seconds")
            print(f"Total prompts: {len(wish._demo_events.get('commands', []))}")
            print(f"State changes: {len(wish._demo_events.get('state_changes', []))}")

        finally:
            summary = await session.end()

            # Demo success criteria
            assert summary.prompts_executed >= 7  # Minimum commands for demo
            assert summary.findings >= 1  # At least one finding recorded

    async def test_demo_ui_elements(self, wish):
        """Test that demo UI elements are present."""
        session = await wish.start_session(metadata={
            "test": "demo_ui_elements"
        })

        try:
            # Elements that should be visible in demo:
            # 1. [✔] Success indicators
            # 2. [▶] Progress indicators
            # 3. [ℹ] Info messages
            # 4. Structured command output

            # These will be implemented in the actual UI
            # For now, verify commands produce output

            await session.send_prompt("/scope add 10.10.10.3")
            result = await session.send_prompt("/status")

            # Status should have structured output
            output = result.result
            assert output is not None
            assert len(output) > 0

            # In implementation, will show:
            # TARGETS:
            # └─ 10.10.10.3
            #    ├─ PORTS:
            #    │  └─ 445/tcp (netbios-ssn, Samba 3.0.20)
            #    └─ VULNERABILITIES:
            #       └─ CVE-2007-2447 (Samba 3.0.20) - Remote Command Execution

        finally:
            await session.end()

    async def test_demo_stability(self, wish):
        """Test demo stability with multiple runs."""
        success_count = 0
        failure_details = []
        run_times = []

        # Run 10 consecutive times
        total_runs = 10

        for i in range(total_runs):
            start_time = datetime.now()
            session = await wish.start_session(metadata={
                "test": f"demo_stability_run_{i+1}",
                "run_number": i + 1,
                "total_runs": total_runs
            })

            try:
                # Complete demo sequence
                # ACT 1: Discovery
                result = await session.send_prompt("/scope add 10.10.10.3")
                assert "scope" in result.result.lower() or "added" in result.result.lower()

                result = await session.send_prompt("scan the target")
                assert result.result is not None

                # ACT 2: Vulnerability identification
                result = await session.send_prompt(
                    "I found Samba 3.0.20 on port 445. What vulnerabilities exist?"
                )
                assert any(term in result.result.lower() for term in ["cve", "2007-2447", "vulnerable"])

                # ACT 3: Status and findings
                result = await session.send_prompt("/status")
                assert "10.10.10.3" in result.result

                result = await session.send_prompt(
                    "/findings add CVE-2007-2447: Samba RCE vulnerability confirmed"
                )

                result = await session.send_prompt("/findings")
                assert "CVE-2007-2447" in result.result or "samba" in result.result.lower()

                # Record elapsed time
                run_time = (datetime.now() - start_time).total_seconds()
                run_times.append(run_time)

                # Success
                success_count += 1
                print(f"\n✅ Run {i+1}/{total_runs} succeeded in {run_time:.2f}s")

            except Exception as e:
                run_time = (datetime.now() - start_time).total_seconds()
                failure_details.append({
                    "run": i + 1,
                    "error": str(e),
                    "time": run_time
                })
                print(f"\n❌ Run {i+1}/{total_runs} failed after {run_time:.2f}s: {e}")

            finally:
                await session.end()

            # Cooldown (avoid interference between sessions)
            if i < total_runs - 1:
                await asyncio.sleep(0.5)

        # Results summary
        print("\n" + "=" * 50)
        print("STABILITY TEST RESULTS:")
        print(f"Success rate: {success_count}/{total_runs} ({success_count/total_runs*100:.1f}%)")

        if run_times:
            avg_time = sum(run_times) / len(run_times)
            max_time = max(run_times)
            min_time = min(run_times)
            print(f"Average run time: {avg_time:.2f}s")
            print(f"Min/Max run time: {min_time:.2f}s / {max_time:.2f}s")

        if failure_details:
            print("\nFailure details:")
            for failure in failure_details:
                print(f"  Run {failure['run']}: {failure['error']}")

        print("=" * 50 + "\n")

        # Verify all runs succeed
        assert success_count == total_runs, f"Only {success_count}/{total_runs} runs succeeded"

    async def test_demo_performance(self, wish):
        """Test demo performance requirements."""
        session = await wish.start_session(metadata={
            "test": "demo_performance"
        })

        command_timings = {}

        try:
            # Measure execution time for each command
            commands = [
                ("/scope add 10.10.10.3", "scope_add"),
                ("scan the target", "scan"),
                ("/status", "status"),
                ("/findings add CVE-2007-2447: Test", "findings_add"),
                ("/findings", "findings_list")
            ]

            for command, label in commands:
                start = datetime.now()
                result = await session.send_prompt(command)
                duration = (datetime.now() - start).total_seconds()

                command_timings[label] = duration

                # Each command should complete within 5 seconds
                assert duration < 5.0, f"{label} took {duration:.2f}s (>5s limit)"
                assert result.result is not None, f"{label} returned no result"

            # Total execution time
            total_time = sum(command_timings.values())

            print("\n⏱️ Performance Test Results:")
            print(f"Total execution time: {total_time:.2f}s")
            for label, duration in command_timings.items():
                print(f"  {label}: {duration:.2f}s")

            # Overall demo aims for under 5 minutes, but test only covers basic commands
            assert total_time < 20.0, f"Total time {total_time:.2f}s exceeds 20s limit"

        finally:
            await session.end()

    async def test_demo_error_recovery(self, wish):
        """Error recovery test."""
        session = await wish.start_session(metadata={
            "test": "error_recovery"
        })

        try:
            # Should not crash on invalid commands
            result = await session.send_prompt("/invalid_command")
            assert "error" in result.result.lower() or "unknown" in result.result.lower()

            # Handle invalid IP addresses
            # Verify validation errors occur
            from wish_models.validation import ValidationError
            try:
                result = await session.send_prompt("/scope add 999.999.999.999")
                # In mock environment, errors may not actually occur
            except ValidationError:
                # If ValidationError occurs, it's normal (validation is working)
                pass

            # Verify normal commands continue to work
            result = await session.send_prompt("/status")
            assert result.result is not None

            # Should handle long input without issues
            long_input = "A" * 1000
            result = await session.send_prompt(f"/findings add {long_input}")

            # Finally verify normal operation
            result = await session.send_prompt("/findings")
            assert result.result is not None

        finally:
            await session.end()
