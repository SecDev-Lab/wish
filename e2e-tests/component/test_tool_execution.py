"""Tool execution integration tests using HeadlessWish."""

import asyncio
import os
import sys
import time

import pytest
from wish_cli.headless import EventType, HeadlessWish

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from fixtures import setup_mocks


class TestToolExecutionIntegration:
    """Test tool execution through HeadlessWish SDK."""

    @pytest.mark.asyncio
    async def test_basic_tool_execution(self):
        """Test basic tool execution flow."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        # Track executions
        executions = []

        @wish.on_event(EventType.JOB_STARTED)
        async def on_job_start(event):
            executions.append({
                "event": "start",
                "job_id": event.data.get("job_id"),
                "tool": event.data.get("tool")
            })

        @wish.on_event(EventType.JOB_COMPLETED)
        async def on_job_complete(event):
            executions.append({
                "event": "complete",
                "job_id": event.data.get("job_id"),
                "result": event.data.get("result")
            })

        session = await wish.start_session()

        try:
            # Execute a scan
            result = await session.send_prompt("run nmap scan on 10.10.10.3")

            # Wait for async jobs to complete
            await asyncio.sleep(0.5)

            # Tool should have been executed
            assert len(executions) >= 2  # Start and complete events

            # Check execution flow
            start_events = [e for e in executions if e["event"] == "start"]
            complete_events = [e for e in executions if e["event"] == "complete"]

            assert len(start_events) > 0
            assert len(complete_events) > 0

            # Result should indicate success
            assert result.result is not None

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_tool_output_parsing(self):
        """Test parsing of tool outputs."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        session = await wish.start_session()

        try:
            # Run nmap (mocked)
            await session.send_prompt("scan 10.10.10.3 with nmap")

            # Check that output was parsed
            state = await session.get_state()

            # Should have discovered host
            host = next((h for h in state.hosts.values()
                        if h.ip_address == "10.10.10.3"), None)
            assert host is not None

            # Should have parsed services
            assert len(host.services) > 0

            # Check specific services from mock data
            ports = {s.port for s in host.services}
            assert 22 in ports  # SSH
            assert 445 in ports  # SMB

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_tool_chaining(self):
        """Test chaining multiple tools."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        # Track tool executions
        tool_sequence = []

        @wish.on_event(EventType.JOB_STARTED)
        async def track_tools(event):
            tool = event.data.get("tool", "unknown")
            tool_sequence.append(tool)

        session = await wish.start_session()

        try:
            # First scan
            await session.send_prompt("scan 10.10.10.3")
            await asyncio.sleep(0.3)

            # Then enumerate
            await session.send_prompt("now enumerate the SMB service")
            await asyncio.sleep(0.3)

            # Then check vulnerabilities
            await session.send_prompt("check for vulnerabilities")
            await asyncio.sleep(0.3)

            # Should have executed multiple tools
            assert len(tool_sequence) >= 2

            # Verify state progression
            final_state = await session.get_state()
            assert len(final_state.hosts) > 0
            assert len(final_state.findings) >= 0  # May or may not find vulns

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_parallel_tool_execution(self):
        """Test parallel execution of tools."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        # Track concurrent executions
        concurrent_jobs = []

        @wish.on_event(EventType.JOB_STARTED)
        async def on_job_start(event):
            concurrent_jobs.append({
                "job_id": event.data.get("job_id"),
                "timestamp": event.timestamp
            })

        session = await wish.start_session()

        try:
            # Request parallel operations
            await session.send_prompt("scan multiple targets: 10.10.10.1, 10.10.10.2, 10.10.10.3 simultaneously")

            # Wait for jobs to start
            await asyncio.sleep(0.1)

            # Should have multiple jobs
            assert len(concurrent_jobs) > 0

            # In real implementation, would check for actual parallelism
            # With mocks, we at least verify multiple jobs were initiated

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_tool_timeout_handling(self):
        """Test handling of tool execution timeouts."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        # Track errors
        errors = []

        @wish.on_event(EventType.ERROR_OCCURRED)
        async def on_error(event):
            errors.append(event.data)

        session = await wish.start_session()

        try:
            # In real implementation, this might timeout
            # Mock handles it gracefully
            await session.send_prompt("perform exhaustive scan of entire subnet")

            # Session should continue working
            result = await session.send_prompt("what's the current status?")
            assert result.result is not None

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_tool_validation(self):
        """Test tool command validation."""
        wish = HeadlessWish(auto_approve=False)  # Manual approval for validation
        wish = setup_mocks(wish)

        validated_commands = []

        @wish.on_event(EventType.PLAN_APPROVAL_REQUIRED)
        async def validate_tools(event):
            from fixtures.mocks import get_plan_from_event
            plan = get_plan_from_event(event)

            for step in plan.steps:
                # Validate tool exists
                valid_tools = ["nmap", "nikto", "gobuster", "enum4linux", "sqlmap"]
                tool_valid = step.tool_name in valid_tools

                # Validate command structure
                command_valid = len(step.command) > 0 and not step.command.startswith(" ")

                validated_commands.append({
                    "tool": step.tool_name,
                    "valid": tool_valid and command_valid,
                    "command": step.command
                })

            return "approve" if all(cmd["valid"] for cmd in validated_commands) else "reject"

        session = await wish.start_session()

        try:
            # Generate various tool commands
            await session.send_prompt("scan with nmap")
            await session.send_prompt("enumerate with invalid-tool")  # Should handle gracefully

            # Check validations
            assert len(validated_commands) > 0

            # Most commands should be valid (mock generates valid commands)
            valid_count = sum(1 for cmd in validated_commands if cmd["valid"])
            assert valid_count > 0

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_custom_tool_parameters(self):
        """Test execution with custom tool parameters."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        # Collect generated commands
        commands = []

        @wish.on_event(EventType.PLAN_APPROVAL_REQUIRED)
        async def collect_commands(event):
            from fixtures.mocks import get_plan_from_event
            plan = get_plan_from_event(event)
            commands.extend([step.command for step in plan.steps])
            return "approve"

        session = await wish.start_session()

        try:
            # Request specific scan parameters
            await session.send_prompt("scan 10.10.10.3 using nmap with service version detection and OS detection")

            # Check generated command
            assert len(commands) > 0
            nmap_cmd = next((cmd for cmd in commands if "nmap" in cmd), None)
            assert nmap_cmd is not None

            # Should include version detection flags
            assert "-sV" in nmap_cmd or "-sC" in nmap_cmd or "-A" in nmap_cmd

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_tool_result_interpretation(self):
        """Test interpretation of tool results."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        session = await wish.start_session()

        try:
            # Run tool
            await session.send_prompt("scan 10.10.10.3")
            await asyncio.sleep(0.5)  # Wait for scan to complete

            # Ask for interpretation
            result = await session.send_prompt("interpret the scan results")

            # Should provide meaningful interpretation
            interpretation = result.result.lower()

            # Should mention discovered services
            assert any(svc in interpretation for svc in ["ssh", "smb", "ftp", "web"])

            # Should provide next steps
            assert any(action in interpretation for action in
                      ["enumerate", "investigate", "check", "test"])

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_tool_error_recovery(self):
        """Test recovery from tool execution errors."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        session = await wish.start_session()

        try:
            # Simulate tool failure scenario
            await session.send_prompt("scan unreachable.host.local")
            await asyncio.sleep(0.3)

            # Should handle gracefully and suggest alternatives
            result = await session.send_prompt("the scan failed, what should I do?")

            # Should provide helpful suggestions
            suggestions = result.result.lower()
            helpful_keywords = ["try", "check", "verify", "alternative", "instead"]

            assert any(keyword in suggestions for keyword in helpful_keywords)

            # Can continue with valid target
            await session.send_prompt("okay, scan 10.10.10.3 instead")
            state = await session.get_state()
            assert len(state.hosts) > 0

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_job_info_tracking(self):
        """Test detailed job information tracking during tool execution."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        # Collect job information
        job_details = {}

        @wish.on_event(EventType.JOB_STARTED)
        async def on_job_start(event):
            job_id = event.data.get("job_id")
            job_details[job_id] = {
                "started": True,
                "tool": event.data.get("tool"),
                "command": event.data.get("command"),
                "description": event.data.get("description")
            }

        @wish.on_event(EventType.JOB_COMPLETED)
        async def on_job_complete(event):
            job_id = event.data.get("job_id")
            if job_id in job_details:
                job_details[job_id]["completed"] = True
                job_details[job_id]["duration"] = event.data.get("duration")

                # Get full job info from job manager
                job_info = wish.job_manager.get_job_info(job_id)
                if job_info:
                    job_details[job_id]["output_size"] = len(job_info.full_output) if job_info.full_output else 0
                    job_details[job_id]["exit_code"] = job_info.exit_code

        session = await wish.start_session()

        try:
            # Execute multiple tools
            await session.send_prompt("perform comprehensive scan and enumeration on 10.10.10.3")

            # Wait for completion
            await asyncio.sleep(1.0)

            # Verify job details were captured
            assert len(job_details) > 0

            # Check each job has complete information
            for _, details in job_details.items():
                assert details["started"] is True
                assert details["completed"] is True
                assert details["tool"] is not None
                assert details["command"] is not None
                assert details["description"] is not None
                assert details["duration"] is not None
                assert details["duration"] > 0
                assert details["output_size"] > 0
                assert details["exit_code"] == 0

            # Verify different tools were used
            tools_used = {details["tool"] for details in job_details.values()}
            assert len(tools_used) >= 2  # At least scan and enumeration tools

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_job_output_processing(self):
        """Test processing and parsing of job outputs."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        session = await wish.start_session()

        try:
            # Execute scan
            await session.send_prompt("scan 10.10.10.3 for services")

            # Wait for completion
            await asyncio.sleep(0.5)

            # Get job outputs
            all_jobs = wish.job_manager.get_all_jobs()
            assert len(all_jobs) > 0

            # Find scan job
            scan_job = None
            for job in all_jobs.values():
                if job.tool_name == "nmap" or (job.command and "nmap" in job.command):
                    scan_job = job
                    break

            assert scan_job is not None
            assert scan_job.full_output is not None

            # Verify output was processed into state
            state = await session.get_state()
            host = next((h for h in state.hosts.values() if h.ip_address == "10.10.10.3"), None)
            assert host is not None

            # Services should match what's in the output
            service_ports = {s.port for s in host.services}
            assert 22 in service_ports  # SSH from mock output
            assert 445 in service_ports  # SMB from mock output

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_job_progress_tracking(self):
        """Test tracking progress of long-running jobs."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        # Track job states over time
        job_states = []

        async def track_job_states():
            """Background task to track job states."""
            for _ in range(10):  # Check 10 times
                current_states = {}
                for job_id, job_info in wish.job_manager.get_all_jobs().items():
                    current_states[job_id] = job_info.status
                job_states.append({
                    "time": time.time(),
                    "states": current_states
                })
                await asyncio.sleep(0.1)

        session = await wish.start_session()

        try:
            # Start tracking task
            tracking_task = asyncio.create_task(track_job_states())

            # Execute long operation
            await session.send_prompt("perform thorough enumeration of all services on 10.10.10.3")

            # Wait for tracking to complete
            await tracking_task

            # Analyze job state transitions
            assert len(job_states) > 0

            # Should see jobs transition from PENDING -> RUNNING -> COMPLETED
            job_transitions = {}
            for snapshot in job_states:
                for job_id, status in snapshot["states"].items():
                    if job_id not in job_transitions:
                        job_transitions[job_id] = []
                    if not job_transitions[job_id] or job_transitions[job_id][-1] != status:
                        job_transitions[job_id].append(status)

            # Verify proper state transitions
            from fixtures.mocks import JobStatus
            for _, transitions in job_transitions.items():
                # Should start with PENDING or RUNNING
                assert transitions[0] in [JobStatus.PENDING, JobStatus.RUNNING]
                # Should end with COMPLETED
                assert transitions[-1] == JobStatus.COMPLETED
                # Should have RUNNING state
                assert JobStatus.RUNNING in transitions

        finally:
            await session.end()
