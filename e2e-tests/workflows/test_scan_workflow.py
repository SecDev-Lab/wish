"""Scan workflow integration tests using HeadlessWish."""

import asyncio
import os
import sys

import pytest
from wish_cli.headless import EventType, HeadlessWish

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from fixtures import HTB_LAME_SCENARIO, MockEventCollector, setup_mocks


class TestScanWorkflow:
    """Test complete scan workflows through HeadlessWish SDK."""

    @pytest.mark.asyncio
    async def test_scan_to_suggestion_workflow(self):
        """Test scan → state update → AI suggestion workflow."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        # Collect events
        collector = MockEventCollector()

        @wish.on_event(EventType.JOB_STARTED)
        async def on_job_start(event):
            collector.collect_all(event)

        @wish.on_event(EventType.JOB_COMPLETED)
        async def on_job_complete(event):
            collector.collect_all(event)

        session = await wish.start_session()

        try:
            # Step 1: Set target
            result = await session.send_prompt("set target 10.10.10.3")
            assert len(result.state_after.targets) == 1

            # Step 2: Perform scan
            result = await session.send_prompt("scan the network for open ports")

            # Verify scan was executed
            job_starts = collector.get_events_by_type(EventType.JOB_STARTED.value)
            assert len(job_starts) > 0

            # Verify state was updated with discovered hosts
            state = await session.get_state()
            assert len(state.hosts) > 0

            # Find the scanned host
            host = next((h for h in state.hosts.values()
                        if h.ip_address == "10.10.10.3"), None)
            assert host is not None
            assert len(host.services) > 0

            # Step 3: Ask for next steps
            result = await session.send_prompt("what should I do next?")

            # AI should suggest enumeration based on discovered services
            assert "enumerate" in result.result.lower() or "service" in result.result.lower()

        finally:
            summary = await session.end()
            assert summary.hosts_discovered > 0

    @pytest.mark.asyncio
    async def test_plan_approval_workflow(self):
        """Test plan generation → approval → execution workflow."""
        wish = HeadlessWish(auto_approve=False)  # Manual approval
        wish = setup_mocks(wish)

        plans_reviewed = []

        @wish.on_event(EventType.PLAN_APPROVAL_REQUIRED)
        async def review_plan(event):
            from fixtures.mocks import get_plan_from_event
            plan = get_plan_from_event(event)
            plans_reviewed.append(plan)

            # Validate plan before approval
            assert plan.description is not None
            assert len(plan.steps) > 0

            # Check if it's a scan plan
            if any("scan" in step.purpose.lower() for step in plan.steps):
                return "approve"
            else:
                return "reject"

        session = await wish.start_session()

        try:
            # This should generate a plan and request approval
            result = await session.send_prompt("perform initial reconnaissance on 10.10.10.3")

            # Plan should have been reviewed
            assert len(plans_reviewed) > 0
            plan = plans_reviewed[0]

            # Verify plan was for reconnaissance
            assert "recon" in plan.description.lower() or "scan" in plan.description.lower()

            # Result should indicate execution
            assert result.result is not None

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_enhanced_parallel_scan_workflow(self):
        """Test enhanced parallel scanning with job management."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        # Track detailed job execution
        job_metrics = {
            "started": [],
            "completed": [],
            "max_concurrent": 0,
            "current_running": 0
        }

        @wish.on_event(EventType.JOB_STARTED)
        async def on_job_start(event):
            job_metrics["started"].append({
                "job_id": event.data.get("job_id"),
                "time": event.timestamp,
                "tool": event.data.get("tool")
            })
            job_metrics["current_running"] += 1
            job_metrics["max_concurrent"] = max(job_metrics["max_concurrent"],
                                               job_metrics["current_running"])

        @wish.on_event(EventType.JOB_COMPLETED)
        async def on_job_complete(event):
            job_metrics["completed"].append({
                "job_id": event.data.get("job_id"),
                "time": event.timestamp,
                "duration": event.data.get("duration")
            })
            job_metrics["current_running"] -= 1

        session = await wish.start_session()

        try:
            # Request parallel scans of multiple targets
            await session.send_prompt("scan these targets simultaneously: 10.10.10.1-5")

            # Wait for all jobs to complete
            await asyncio.sleep(1.5)

            # Verify parallel execution
            assert len(job_metrics["started"]) >= 3  # Multiple scans
            assert job_metrics["max_concurrent"] > 1  # Actual parallelism

            # Verify all jobs completed
            assert len(job_metrics["completed"]) == len(job_metrics["started"])

            # Check timing - jobs should overlap
            if len(job_metrics["started"]) >= 2:
                # Sort by start time
                sorted_starts = sorted(job_metrics["started"], key=lambda x: x["time"])
                sorted_completes = sorted(job_metrics["completed"], key=lambda x: x["time"])

                # First job should complete after second job starts (overlap)
                if len(sorted_starts) >= 2 and len(sorted_completes) >= 1:
                    first_complete = next((c for c in sorted_completes
                                         if c["job_id"] == sorted_starts[0]["job_id"]), None)
                    if first_complete:
                        assert sorted_starts[1]["time"] < first_complete["time"], \
                            "Jobs should execute in parallel"

            # Verify scan results
            state = await session.get_state()
            assert len(state.hosts) >= 1  # At least one host discovered

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_job_dependency_workflow(self):
        """Test workflows with job dependencies."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        # Track job execution order
        execution_order = []

        @wish.on_event(EventType.JOB_STARTED)
        async def track_execution(event):
            execution_order.append({
                "job_id": event.data.get("job_id"),
                "tool": event.data.get("tool"),
                "command": event.data.get("command")
            })

        session = await wish.start_session()

        try:
            # Execute workflow with natural dependencies
            await session.send_prompt("first scan 10.10.10.3, then enumerate the discovered services")

            # Wait for completion
            await asyncio.sleep(1.0)

            # Verify execution order
            assert len(execution_order) >= 2

            # Scan should come before enumeration
            scan_idx = next((i for i, job in enumerate(execution_order)
                           if "nmap" in str(job.get("tool", ""))), None)
            enum_idx = next((i for i, job in enumerate(execution_order)
                           if any(tool in str(job.get("tool", ""))
                                for tool in ["enum4linux", "gobuster", "nikto"])), None)

            if scan_idx is not None and enum_idx is not None:
                assert scan_idx < enum_idx, "Scan should execute before enumeration"

            # Verify state progression
            state = await session.get_state()
            assert len(state.hosts) > 0

            # Should have discovered services
            total_services = sum(len(h.services) for h in state.hosts.values())
            assert total_services > 0

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_concurrent_job_limit_workflow(self):
        """Test respecting concurrent job limits in workflows."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        # Set a low limit for testing
        wish.job_manager.max_concurrent_jobs = 2

        # Track concurrent execution
        concurrent_tracking = []

        @wish.on_event(EventType.JOB_STARTED)
        async def on_start(event):
            running = len(wish.job_manager.get_running_jobs())
            concurrent_tracking.append(("start", running))

        @wish.on_event(EventType.JOB_COMPLETED)
        async def on_complete(event):
            running = len(wish.job_manager.get_running_jobs())
            concurrent_tracking.append(("complete", running))

        session = await wish.start_session()

        try:
            # Submit many parallel tasks
            await session.send_prompt("scan the entire 10.10.10.0/24 subnet quickly")

            # Wait for processing
            await asyncio.sleep(2.0)

            # Verify limit was respected
            max_concurrent_observed = max((count for event, count in concurrent_tracking
                                         if event == "start"), default=0)
            assert max_concurrent_observed <= 2, \
                f"Concurrent limit exceeded: {max_concurrent_observed} > 2"

            # All jobs should eventually complete
            all_jobs = wish.job_manager.get_all_jobs()
            completed = sum(1 for job in all_jobs.values()
                          if job.status == "completed")
            assert completed >= 1  # At least some jobs completed

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_job_output_aggregation_workflow(self):
        """Test aggregating outputs from multiple parallel jobs."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        session = await wish.start_session()

        try:
            # Execute parallel scans
            await session.send_prompt("scan 10.10.10.1, 10.10.10.2, and 10.10.10.3 and summarize all findings")

            # Wait for completion
            await asyncio.sleep(1.5)

            # Get aggregated results
            state = await session.get_state()

            # Should have results from multiple hosts
            assert len(state.hosts) >= 1

            # Collect all services across hosts
            all_services = []
            for host in state.hosts.values():
                all_services.extend(host.services)

            # Should have discovered services
            assert len(all_services) > 0

            # Check job outputs were preserved
            all_jobs = wish.job_manager.get_all_jobs()
            scan_jobs = [job for job in all_jobs.values()
                        if job.tool_name == "nmap" or (job.command and "nmap" in job.command)]

            # Each scan job should have output
            for job in scan_jobs:
                assert job.full_output is not None
                assert len(job.full_output) > 0

            # Ask for summary
            result = await session.send_prompt("summarize what was found across all targets")

            # Summary should mention multiple aspects
            summary = result.result.lower()
            assert any(word in summary for word in ["hosts", "services", "ports"])

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_multi_target_scan_workflow(self):
        """Test scanning multiple targets in sequence."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        session = await wish.start_session()

        try:
            # Set multiple targets
            await session.send_prompt("set targets 10.10.10.1-10.10.10.5")

            # Scan all targets
            result = await session.send_prompt("scan all targets for common services")

            # Should have discovered multiple hosts
            state = await session.get_state()
            assert len(state.hosts) >= 1  # At least one host discovered

            # Each host should have services
            for host in state.hosts.values():
                assert len(host.services) > 0
                assert host.discovered_by is not None

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_enhanced_parallel_scan_workflow(self):
        """Test enhanced parallel scanning with job management."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        # Track detailed job execution
        job_metrics = {
            "started": [],
            "completed": [],
            "max_concurrent": 0,
            "current_running": 0
        }

        @wish.on_event(EventType.JOB_STARTED)
        async def on_job_start(event):
            job_metrics["started"].append({
                "job_id": event.data.get("job_id"),
                "time": event.timestamp,
                "tool": event.data.get("tool")
            })
            job_metrics["current_running"] += 1
            job_metrics["max_concurrent"] = max(job_metrics["max_concurrent"],
                                               job_metrics["current_running"])

        @wish.on_event(EventType.JOB_COMPLETED)
        async def on_job_complete(event):
            job_metrics["completed"].append({
                "job_id": event.data.get("job_id"),
                "time": event.timestamp,
                "duration": event.data.get("duration")
            })
            job_metrics["current_running"] -= 1

        session = await wish.start_session()

        try:
            # Request parallel scans of multiple targets
            await session.send_prompt("scan these targets simultaneously: 10.10.10.1-5")

            # Wait for all jobs to complete
            await asyncio.sleep(1.5)

            # Verify parallel execution
            assert len(job_metrics["started"]) >= 3  # Multiple scans
            assert job_metrics["max_concurrent"] > 1  # Actual parallelism

            # Verify all jobs completed
            assert len(job_metrics["completed"]) == len(job_metrics["started"])

            # Check timing - jobs should overlap
            if len(job_metrics["started"]) >= 2:
                # Sort by start time
                sorted_starts = sorted(job_metrics["started"], key=lambda x: x["time"])
                sorted_completes = sorted(job_metrics["completed"], key=lambda x: x["time"])

                # First job should complete after second job starts (overlap)
                if len(sorted_starts) >= 2 and len(sorted_completes) >= 1:
                    first_complete = next((c for c in sorted_completes
                                         if c["job_id"] == sorted_starts[0]["job_id"]), None)
                    if first_complete:
                        assert sorted_starts[1]["time"] < first_complete["time"], \
                            "Jobs should execute in parallel"

            # Verify scan results
            state = await session.get_state()
            assert len(state.hosts) >= 1  # At least one host discovered

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_job_dependency_workflow(self):
        """Test workflows with job dependencies."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        # Track job execution order
        execution_order = []

        @wish.on_event(EventType.JOB_STARTED)
        async def track_execution(event):
            execution_order.append({
                "job_id": event.data.get("job_id"),
                "tool": event.data.get("tool"),
                "command": event.data.get("command")
            })

        session = await wish.start_session()

        try:
            # Execute workflow with natural dependencies
            await session.send_prompt("first scan 10.10.10.3, then enumerate the discovered services")

            # Wait for completion
            await asyncio.sleep(1.0)

            # Verify execution order
            assert len(execution_order) >= 2

            # Scan should come before enumeration
            scan_idx = next((i for i, job in enumerate(execution_order)
                           if "nmap" in str(job.get("tool", ""))), None)
            enum_idx = next((i for i, job in enumerate(execution_order)
                           if any(tool in str(job.get("tool", ""))
                                for tool in ["enum4linux", "gobuster", "nikto"])), None)

            if scan_idx is not None and enum_idx is not None:
                assert scan_idx < enum_idx, "Scan should execute before enumeration"

            # Verify state progression
            state = await session.get_state()
            assert len(state.hosts) > 0

            # Should have discovered services
            total_services = sum(len(h.services) for h in state.hosts.values())
            assert total_services > 0

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_concurrent_job_limit_workflow(self):
        """Test respecting concurrent job limits in workflows."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        # Set a low limit for testing
        wish.job_manager.max_concurrent_jobs = 2

        # Track concurrent execution
        concurrent_tracking = []

        @wish.on_event(EventType.JOB_STARTED)
        async def on_start(event):
            running = len(wish.job_manager.get_running_jobs())
            concurrent_tracking.append(("start", running))

        @wish.on_event(EventType.JOB_COMPLETED)
        async def on_complete(event):
            running = len(wish.job_manager.get_running_jobs())
            concurrent_tracking.append(("complete", running))

        session = await wish.start_session()

        try:
            # Submit many parallel tasks
            await session.send_prompt("scan the entire 10.10.10.0/24 subnet quickly")

            # Wait for processing
            await asyncio.sleep(2.0)

            # Verify limit was respected
            max_concurrent_observed = max((count for event, count in concurrent_tracking
                                         if event == "start"), default=0)
            assert max_concurrent_observed <= 2, \
                f"Concurrent limit exceeded: {max_concurrent_observed} > 2"

            # All jobs should eventually complete
            all_jobs = wish.job_manager.get_all_jobs()
            completed = sum(1 for job in all_jobs.values()
                          if job.status == "completed")
            assert completed >= 1  # At least some jobs completed

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_job_output_aggregation_workflow(self):
        """Test aggregating outputs from multiple parallel jobs."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        session = await wish.start_session()

        try:
            # Execute parallel scans
            await session.send_prompt("scan 10.10.10.1, 10.10.10.2, and 10.10.10.3 and summarize all findings")

            # Wait for completion
            await asyncio.sleep(1.5)

            # Get aggregated results
            state = await session.get_state()

            # Should have results from multiple hosts
            assert len(state.hosts) >= 1

            # Collect all services across hosts
            all_services = []
            for host in state.hosts.values():
                all_services.extend(host.services)

            # Should have discovered services
            assert len(all_services) > 0

            # Check job outputs were preserved
            all_jobs = wish.job_manager.get_all_jobs()
            scan_jobs = [job for job in all_jobs.values()
                        if job.tool_name == "nmap" or (job.command and "nmap" in job.command)]

            # Each scan job should have output
            for job in scan_jobs:
                assert job.full_output is not None
                assert len(job.full_output) > 0

            # Ask for summary
            result = await session.send_prompt("summarize what was found across all targets")

            # Summary should mention multiple aspects
            summary = result.result.lower()
            assert any(word in summary for word in ["hosts", "services", "ports"])

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_targeted_service_scan(self):
        """Test scanning for specific services."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        # Track plan details
        collector = MockEventCollector()

        @wish.on_event(EventType.PLAN_APPROVAL_REQUIRED)
        async def collect_plans(event):
            collector.collect_plan_approval(event)
            return "approve"

        session = await wish.start_session()

        try:
            # Request specific service scan
            await session.send_prompt("scan 10.10.10.3 specifically for SMB and web services")

            # Check generated plan
            assert len(collector.plan_approvals) > 0
            plan = collector.plan_approvals[0]

            # Should have targeted scan commands
            commands = " ".join(step.command for step in plan.steps)
            assert any(port in commands for port in ["445", "139", "80", "443"])

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_enhanced_parallel_scan_workflow(self):
        """Test enhanced parallel scanning with job management."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        # Track detailed job execution
        job_metrics = {
            "started": [],
            "completed": [],
            "max_concurrent": 0,
            "current_running": 0
        }

        @wish.on_event(EventType.JOB_STARTED)
        async def on_job_start(event):
            job_metrics["started"].append({
                "job_id": event.data.get("job_id"),
                "time": event.timestamp,
                "tool": event.data.get("tool")
            })
            job_metrics["current_running"] += 1
            job_metrics["max_concurrent"] = max(job_metrics["max_concurrent"],
                                               job_metrics["current_running"])

        @wish.on_event(EventType.JOB_COMPLETED)
        async def on_job_complete(event):
            job_metrics["completed"].append({
                "job_id": event.data.get("job_id"),
                "time": event.timestamp,
                "duration": event.data.get("duration")
            })
            job_metrics["current_running"] -= 1

        session = await wish.start_session()

        try:
            # Request parallel scans of multiple targets
            await session.send_prompt("scan these targets simultaneously: 10.10.10.1-5")

            # Wait for all jobs to complete
            await asyncio.sleep(1.5)

            # Verify parallel execution
            assert len(job_metrics["started"]) >= 3  # Multiple scans
            assert job_metrics["max_concurrent"] > 1  # Actual parallelism

            # Verify all jobs completed
            assert len(job_metrics["completed"]) == len(job_metrics["started"])

            # Check timing - jobs should overlap
            if len(job_metrics["started"]) >= 2:
                # Sort by start time
                sorted_starts = sorted(job_metrics["started"], key=lambda x: x["time"])
                sorted_completes = sorted(job_metrics["completed"], key=lambda x: x["time"])

                # First job should complete after second job starts (overlap)
                if len(sorted_starts) >= 2 and len(sorted_completes) >= 1:
                    first_complete = next((c for c in sorted_completes
                                         if c["job_id"] == sorted_starts[0]["job_id"]), None)
                    if first_complete:
                        assert sorted_starts[1]["time"] < first_complete["time"], \
                            "Jobs should execute in parallel"

            # Verify scan results
            state = await session.get_state()
            assert len(state.hosts) >= 1  # At least one host discovered

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_job_dependency_workflow(self):
        """Test workflows with job dependencies."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        # Track job execution order
        execution_order = []

        @wish.on_event(EventType.JOB_STARTED)
        async def track_execution(event):
            execution_order.append({
                "job_id": event.data.get("job_id"),
                "tool": event.data.get("tool"),
                "command": event.data.get("command")
            })

        session = await wish.start_session()

        try:
            # Execute workflow with natural dependencies
            await session.send_prompt("first scan 10.10.10.3, then enumerate the discovered services")

            # Wait for completion
            await asyncio.sleep(1.0)

            # Verify execution order
            assert len(execution_order) >= 2

            # Scan should come before enumeration
            scan_idx = next((i for i, job in enumerate(execution_order)
                           if "nmap" in str(job.get("tool", ""))), None)
            enum_idx = next((i for i, job in enumerate(execution_order)
                           if any(tool in str(job.get("tool", ""))
                                for tool in ["enum4linux", "gobuster", "nikto"])), None)

            if scan_idx is not None and enum_idx is not None:
                assert scan_idx < enum_idx, "Scan should execute before enumeration"

            # Verify state progression
            state = await session.get_state()
            assert len(state.hosts) > 0

            # Should have discovered services
            total_services = sum(len(h.services) for h in state.hosts.values())
            assert total_services > 0

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_concurrent_job_limit_workflow(self):
        """Test respecting concurrent job limits in workflows."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        # Set a low limit for testing
        wish.job_manager.max_concurrent_jobs = 2

        # Track concurrent execution
        concurrent_tracking = []

        @wish.on_event(EventType.JOB_STARTED)
        async def on_start(event):
            running = len(wish.job_manager.get_running_jobs())
            concurrent_tracking.append(("start", running))

        @wish.on_event(EventType.JOB_COMPLETED)
        async def on_complete(event):
            running = len(wish.job_manager.get_running_jobs())
            concurrent_tracking.append(("complete", running))

        session = await wish.start_session()

        try:
            # Submit many parallel tasks
            await session.send_prompt("scan the entire 10.10.10.0/24 subnet quickly")

            # Wait for processing
            await asyncio.sleep(2.0)

            # Verify limit was respected
            max_concurrent_observed = max((count for event, count in concurrent_tracking
                                         if event == "start"), default=0)
            assert max_concurrent_observed <= 2, \
                f"Concurrent limit exceeded: {max_concurrent_observed} > 2"

            # All jobs should eventually complete
            all_jobs = wish.job_manager.get_all_jobs()
            completed = sum(1 for job in all_jobs.values()
                          if job.status == "completed")
            assert completed >= 1  # At least some jobs completed

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_job_output_aggregation_workflow(self):
        """Test aggregating outputs from multiple parallel jobs."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        session = await wish.start_session()

        try:
            # Execute parallel scans
            await session.send_prompt("scan 10.10.10.1, 10.10.10.2, and 10.10.10.3 and summarize all findings")

            # Wait for completion
            await asyncio.sleep(1.5)

            # Get aggregated results
            state = await session.get_state()

            # Should have results from multiple hosts
            assert len(state.hosts) >= 1

            # Collect all services across hosts
            all_services = []
            for host in state.hosts.values():
                all_services.extend(host.services)

            # Should have discovered services
            assert len(all_services) > 0

            # Check job outputs were preserved
            all_jobs = wish.job_manager.get_all_jobs()
            scan_jobs = [job for job in all_jobs.values()
                        if job.tool_name == "nmap" or (job.command and "nmap" in job.command)]

            # Each scan job should have output
            for job in scan_jobs:
                assert job.full_output is not None
                assert len(job.full_output) > 0

            # Ask for summary
            result = await session.send_prompt("summarize what was found across all targets")

            # Summary should mention multiple aspects
            summary = result.result.lower()
            assert any(word in summary for word in ["hosts", "services", "ports"])

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_scan_with_version_detection(self):
        """Test service version detection workflow."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        session = await wish.start_session()

        try:
            # Scan with version detection
            await session.send_prompt("scan 10.10.10.3 with service version detection")

            # Check discovered services have version info
            state = await session.get_state()
            host = next((h for h in state.hosts.values()
                        if h.ip_address == "10.10.10.3"), None)

            assert host is not None

            # Services should have version information
            services_with_version = [s for s in host.services if s.version]
            assert len(services_with_version) > 0

            # Check specific versions from mock data
            samba_service = next((s for s in host.services if s.port == 445), None)
            assert samba_service is not None
            assert samba_service.product is not None

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_enhanced_parallel_scan_workflow(self):
        """Test enhanced parallel scanning with job management."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        # Track detailed job execution
        job_metrics = {
            "started": [],
            "completed": [],
            "max_concurrent": 0,
            "current_running": 0
        }

        @wish.on_event(EventType.JOB_STARTED)
        async def on_job_start(event):
            job_metrics["started"].append({
                "job_id": event.data.get("job_id"),
                "time": event.timestamp,
                "tool": event.data.get("tool")
            })
            job_metrics["current_running"] += 1
            job_metrics["max_concurrent"] = max(job_metrics["max_concurrent"],
                                               job_metrics["current_running"])

        @wish.on_event(EventType.JOB_COMPLETED)
        async def on_job_complete(event):
            job_metrics["completed"].append({
                "job_id": event.data.get("job_id"),
                "time": event.timestamp,
                "duration": event.data.get("duration")
            })
            job_metrics["current_running"] -= 1

        session = await wish.start_session()

        try:
            # Request parallel scans of multiple targets
            await session.send_prompt("scan these targets simultaneously: 10.10.10.1-5")

            # Wait for all jobs to complete
            await asyncio.sleep(1.5)

            # Verify parallel execution
            assert len(job_metrics["started"]) >= 3  # Multiple scans
            assert job_metrics["max_concurrent"] > 1  # Actual parallelism

            # Verify all jobs completed
            assert len(job_metrics["completed"]) == len(job_metrics["started"])

            # Check timing - jobs should overlap
            if len(job_metrics["started"]) >= 2:
                # Sort by start time
                sorted_starts = sorted(job_metrics["started"], key=lambda x: x["time"])
                sorted_completes = sorted(job_metrics["completed"], key=lambda x: x["time"])

                # First job should complete after second job starts (overlap)
                if len(sorted_starts) >= 2 and len(sorted_completes) >= 1:
                    first_complete = next((c for c in sorted_completes
                                         if c["job_id"] == sorted_starts[0]["job_id"]), None)
                    if first_complete:
                        assert sorted_starts[1]["time"] < first_complete["time"], \
                            "Jobs should execute in parallel"

            # Verify scan results
            state = await session.get_state()
            assert len(state.hosts) >= 1  # At least one host discovered

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_job_dependency_workflow(self):
        """Test workflows with job dependencies."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        # Track job execution order
        execution_order = []

        @wish.on_event(EventType.JOB_STARTED)
        async def track_execution(event):
            execution_order.append({
                "job_id": event.data.get("job_id"),
                "tool": event.data.get("tool"),
                "command": event.data.get("command")
            })

        session = await wish.start_session()

        try:
            # Execute workflow with natural dependencies
            await session.send_prompt("first scan 10.10.10.3, then enumerate the discovered services")

            # Wait for completion
            await asyncio.sleep(1.0)

            # Verify execution order
            assert len(execution_order) >= 2

            # Scan should come before enumeration
            scan_idx = next((i for i, job in enumerate(execution_order)
                           if "nmap" in str(job.get("tool", ""))), None)
            enum_idx = next((i for i, job in enumerate(execution_order)
                           if any(tool in str(job.get("tool", ""))
                                for tool in ["enum4linux", "gobuster", "nikto"])), None)

            if scan_idx is not None and enum_idx is not None:
                assert scan_idx < enum_idx, "Scan should execute before enumeration"

            # Verify state progression
            state = await session.get_state()
            assert len(state.hosts) > 0

            # Should have discovered services
            total_services = sum(len(h.services) for h in state.hosts.values())
            assert total_services > 0

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_concurrent_job_limit_workflow(self):
        """Test respecting concurrent job limits in workflows."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        # Set a low limit for testing
        wish.job_manager.max_concurrent_jobs = 2

        # Track concurrent execution
        concurrent_tracking = []

        @wish.on_event(EventType.JOB_STARTED)
        async def on_start(event):
            running = len(wish.job_manager.get_running_jobs())
            concurrent_tracking.append(("start", running))

        @wish.on_event(EventType.JOB_COMPLETED)
        async def on_complete(event):
            running = len(wish.job_manager.get_running_jobs())
            concurrent_tracking.append(("complete", running))

        session = await wish.start_session()

        try:
            # Submit many parallel tasks
            await session.send_prompt("scan the entire 10.10.10.0/24 subnet quickly")

            # Wait for processing
            await asyncio.sleep(2.0)

            # Verify limit was respected
            max_concurrent_observed = max((count for event, count in concurrent_tracking
                                         if event == "start"), default=0)
            assert max_concurrent_observed <= 2, \
                f"Concurrent limit exceeded: {max_concurrent_observed} > 2"

            # All jobs should eventually complete
            all_jobs = wish.job_manager.get_all_jobs()
            completed = sum(1 for job in all_jobs.values()
                          if job.status == "completed")
            assert completed >= 1  # At least some jobs completed

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_job_output_aggregation_workflow(self):
        """Test aggregating outputs from multiple parallel jobs."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        session = await wish.start_session()

        try:
            # Execute parallel scans
            await session.send_prompt("scan 10.10.10.1, 10.10.10.2, and 10.10.10.3 and summarize all findings")

            # Wait for completion
            await asyncio.sleep(1.5)

            # Get aggregated results
            state = await session.get_state()

            # Should have results from multiple hosts
            assert len(state.hosts) >= 1

            # Collect all services across hosts
            all_services = []
            for host in state.hosts.values():
                all_services.extend(host.services)

            # Should have discovered services
            assert len(all_services) > 0

            # Check job outputs were preserved
            all_jobs = wish.job_manager.get_all_jobs()
            scan_jobs = [job for job in all_jobs.values()
                        if job.tool_name == "nmap" or (job.command and "nmap" in job.command)]

            # Each scan job should have output
            for job in scan_jobs:
                assert job.full_output is not None
                assert len(job.full_output) > 0

            # Ask for summary
            result = await session.send_prompt("summarize what was found across all targets")

            # Summary should mention multiple aspects
            summary = result.result.lower()
            assert any(word in summary for word in ["hosts", "services", "ports"])

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_progressive_scanning(self):
        """Test progressive scanning strategy."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        session = await wish.start_session()

        try:
            # Quick scan first
            await session.send_prompt("do a quick scan of 10.10.10.3")
            initial_state = await session.get_state()
            initial_host_count = len(initial_state.hosts)

            # Then detailed scan
            await session.send_prompt("now do a comprehensive scan of discovered hosts")
            detailed_state = await session.get_state()

            # Should have same or more hosts
            assert len(detailed_state.hosts) >= initial_host_count

            # Services should be discovered
            total_services = sum(len(h.services) for h in detailed_state.hosts.values())
            assert total_services > 0

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_enhanced_parallel_scan_workflow(self):
        """Test enhanced parallel scanning with job management."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        # Track detailed job execution
        job_metrics = {
            "started": [],
            "completed": [],
            "max_concurrent": 0,
            "current_running": 0
        }

        @wish.on_event(EventType.JOB_STARTED)
        async def on_job_start(event):
            job_metrics["started"].append({
                "job_id": event.data.get("job_id"),
                "time": event.timestamp,
                "tool": event.data.get("tool")
            })
            job_metrics["current_running"] += 1
            job_metrics["max_concurrent"] = max(job_metrics["max_concurrent"],
                                               job_metrics["current_running"])

        @wish.on_event(EventType.JOB_COMPLETED)
        async def on_job_complete(event):
            job_metrics["completed"].append({
                "job_id": event.data.get("job_id"),
                "time": event.timestamp,
                "duration": event.data.get("duration")
            })
            job_metrics["current_running"] -= 1

        session = await wish.start_session()

        try:
            # Request parallel scans of multiple targets
            await session.send_prompt("scan these targets simultaneously: 10.10.10.1-5")

            # Wait for all jobs to complete
            await asyncio.sleep(1.5)

            # Verify parallel execution
            assert len(job_metrics["started"]) >= 3  # Multiple scans
            assert job_metrics["max_concurrent"] > 1  # Actual parallelism

            # Verify all jobs completed
            assert len(job_metrics["completed"]) == len(job_metrics["started"])

            # Check timing - jobs should overlap
            if len(job_metrics["started"]) >= 2:
                # Sort by start time
                sorted_starts = sorted(job_metrics["started"], key=lambda x: x["time"])
                sorted_completes = sorted(job_metrics["completed"], key=lambda x: x["time"])

                # First job should complete after second job starts (overlap)
                if len(sorted_starts) >= 2 and len(sorted_completes) >= 1:
                    first_complete = next((c for c in sorted_completes
                                         if c["job_id"] == sorted_starts[0]["job_id"]), None)
                    if first_complete:
                        assert sorted_starts[1]["time"] < first_complete["time"], \
                            "Jobs should execute in parallel"

            # Verify scan results
            state = await session.get_state()
            assert len(state.hosts) >= 1  # At least one host discovered

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_job_dependency_workflow(self):
        """Test workflows with job dependencies."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        # Track job execution order
        execution_order = []

        @wish.on_event(EventType.JOB_STARTED)
        async def track_execution(event):
            execution_order.append({
                "job_id": event.data.get("job_id"),
                "tool": event.data.get("tool"),
                "command": event.data.get("command")
            })

        session = await wish.start_session()

        try:
            # Execute workflow with natural dependencies
            await session.send_prompt("first scan 10.10.10.3, then enumerate the discovered services")

            # Wait for completion
            await asyncio.sleep(1.0)

            # Verify execution order
            assert len(execution_order) >= 2

            # Scan should come before enumeration
            scan_idx = next((i for i, job in enumerate(execution_order)
                           if "nmap" in str(job.get("tool", ""))), None)
            enum_idx = next((i for i, job in enumerate(execution_order)
                           if any(tool in str(job.get("tool", ""))
                                for tool in ["enum4linux", "gobuster", "nikto"])), None)

            if scan_idx is not None and enum_idx is not None:
                assert scan_idx < enum_idx, "Scan should execute before enumeration"

            # Verify state progression
            state = await session.get_state()
            assert len(state.hosts) > 0

            # Should have discovered services
            total_services = sum(len(h.services) for h in state.hosts.values())
            assert total_services > 0

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_concurrent_job_limit_workflow(self):
        """Test respecting concurrent job limits in workflows."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        # Set a low limit for testing
        wish.job_manager.max_concurrent_jobs = 2

        # Track concurrent execution
        concurrent_tracking = []

        @wish.on_event(EventType.JOB_STARTED)
        async def on_start(event):
            running = len(wish.job_manager.get_running_jobs())
            concurrent_tracking.append(("start", running))

        @wish.on_event(EventType.JOB_COMPLETED)
        async def on_complete(event):
            running = len(wish.job_manager.get_running_jobs())
            concurrent_tracking.append(("complete", running))

        session = await wish.start_session()

        try:
            # Submit many parallel tasks
            await session.send_prompt("scan the entire 10.10.10.0/24 subnet quickly")

            # Wait for processing
            await asyncio.sleep(2.0)

            # Verify limit was respected
            max_concurrent_observed = max((count for event, count in concurrent_tracking
                                         if event == "start"), default=0)
            assert max_concurrent_observed <= 2, \
                f"Concurrent limit exceeded: {max_concurrent_observed} > 2"

            # All jobs should eventually complete
            all_jobs = wish.job_manager.get_all_jobs()
            completed = sum(1 for job in all_jobs.values()
                          if job.status == "completed")
            assert completed >= 1  # At least some jobs completed

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_job_output_aggregation_workflow(self):
        """Test aggregating outputs from multiple parallel jobs."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        session = await wish.start_session()

        try:
            # Execute parallel scans
            await session.send_prompt("scan 10.10.10.1, 10.10.10.2, and 10.10.10.3 and summarize all findings")

            # Wait for completion
            await asyncio.sleep(1.5)

            # Get aggregated results
            state = await session.get_state()

            # Should have results from multiple hosts
            assert len(state.hosts) >= 1

            # Collect all services across hosts
            all_services = []
            for host in state.hosts.values():
                all_services.extend(host.services)

            # Should have discovered services
            assert len(all_services) > 0

            # Check job outputs were preserved
            all_jobs = wish.job_manager.get_all_jobs()
            scan_jobs = [job for job in all_jobs.values()
                        if job.tool_name == "nmap" or (job.command and "nmap" in job.command)]

            # Each scan job should have output
            for job in scan_jobs:
                assert job.full_output is not None
                assert len(job.full_output) > 0

            # Ask for summary
            result = await session.send_prompt("summarize what was found across all targets")

            # Summary should mention multiple aspects
            summary = result.result.lower()
            assert any(word in summary for word in ["hosts", "services", "ports"])

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_scan_error_handling(self):
        """Test error handling during scan workflow."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        # Collect errors
        errors = []

        @wish.on_event(EventType.ERROR_OCCURRED)
        async def on_error(event):
            errors.append(event.data)

        session = await wish.start_session()

        try:
            # Try to scan invalid target
            await session.send_prompt("scan invalid.nonexistent.local")

            # Should handle gracefully
            state = await session.get_state()

            # Error should be recorded but session continues
            assert len(errors) > 0  # Error should be recorded through event handler

            # Can continue with valid target
            await session.send_prompt("scan 10.10.10.3 instead")
            state = await session.get_state()
            assert len(state.hosts) > 0

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_enhanced_parallel_scan_workflow(self):
        """Test enhanced parallel scanning with job management."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        # Track detailed job execution
        job_metrics = {
            "started": [],
            "completed": [],
            "max_concurrent": 0,
            "current_running": 0
        }

        @wish.on_event(EventType.JOB_STARTED)
        async def on_job_start(event):
            job_metrics["started"].append({
                "job_id": event.data.get("job_id"),
                "time": event.timestamp,
                "tool": event.data.get("tool")
            })
            job_metrics["current_running"] += 1
            job_metrics["max_concurrent"] = max(job_metrics["max_concurrent"],
                                               job_metrics["current_running"])

        @wish.on_event(EventType.JOB_COMPLETED)
        async def on_job_complete(event):
            job_metrics["completed"].append({
                "job_id": event.data.get("job_id"),
                "time": event.timestamp,
                "duration": event.data.get("duration")
            })
            job_metrics["current_running"] -= 1

        session = await wish.start_session()

        try:
            # Request parallel scans of multiple targets
            await session.send_prompt("scan these targets simultaneously: 10.10.10.1-5")

            # Wait for all jobs to complete
            await asyncio.sleep(1.5)

            # Verify parallel execution
            assert len(job_metrics["started"]) >= 3  # Multiple scans
            assert job_metrics["max_concurrent"] > 1  # Actual parallelism

            # Verify all jobs completed
            assert len(job_metrics["completed"]) == len(job_metrics["started"])

            # Check timing - jobs should overlap
            if len(job_metrics["started"]) >= 2:
                # Sort by start time
                sorted_starts = sorted(job_metrics["started"], key=lambda x: x["time"])
                sorted_completes = sorted(job_metrics["completed"], key=lambda x: x["time"])

                # First job should complete after second job starts (overlap)
                if len(sorted_starts) >= 2 and len(sorted_completes) >= 1:
                    first_complete = next((c for c in sorted_completes
                                         if c["job_id"] == sorted_starts[0]["job_id"]), None)
                    if first_complete:
                        assert sorted_starts[1]["time"] < first_complete["time"], \
                            "Jobs should execute in parallel"

            # Verify scan results
            state = await session.get_state()
            assert len(state.hosts) >= 1  # At least one host discovered

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_job_dependency_workflow(self):
        """Test workflows with job dependencies."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        # Track job execution order
        execution_order = []

        @wish.on_event(EventType.JOB_STARTED)
        async def track_execution(event):
            execution_order.append({
                "job_id": event.data.get("job_id"),
                "tool": event.data.get("tool"),
                "command": event.data.get("command")
            })

        session = await wish.start_session()

        try:
            # Execute workflow with natural dependencies
            await session.send_prompt("first scan 10.10.10.3, then enumerate the discovered services")

            # Wait for completion
            await asyncio.sleep(1.0)

            # Verify execution order
            assert len(execution_order) >= 2

            # Scan should come before enumeration
            scan_idx = next((i for i, job in enumerate(execution_order)
                           if "nmap" in str(job.get("tool", ""))), None)
            enum_idx = next((i for i, job in enumerate(execution_order)
                           if any(tool in str(job.get("tool", ""))
                                for tool in ["enum4linux", "gobuster", "nikto"])), None)

            if scan_idx is not None and enum_idx is not None:
                assert scan_idx < enum_idx, "Scan should execute before enumeration"

            # Verify state progression
            state = await session.get_state()
            assert len(state.hosts) > 0

            # Should have discovered services
            total_services = sum(len(h.services) for h in state.hosts.values())
            assert total_services > 0

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_concurrent_job_limit_workflow(self):
        """Test respecting concurrent job limits in workflows."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        # Set a low limit for testing
        wish.job_manager.max_concurrent_jobs = 2

        # Track concurrent execution
        concurrent_tracking = []

        @wish.on_event(EventType.JOB_STARTED)
        async def on_start(event):
            running = len(wish.job_manager.get_running_jobs())
            concurrent_tracking.append(("start", running))

        @wish.on_event(EventType.JOB_COMPLETED)
        async def on_complete(event):
            running = len(wish.job_manager.get_running_jobs())
            concurrent_tracking.append(("complete", running))

        session = await wish.start_session()

        try:
            # Submit many parallel tasks
            await session.send_prompt("scan the entire 10.10.10.0/24 subnet quickly")

            # Wait for processing
            await asyncio.sleep(2.0)

            # Verify limit was respected
            max_concurrent_observed = max((count for event, count in concurrent_tracking
                                         if event == "start"), default=0)
            assert max_concurrent_observed <= 2, \
                f"Concurrent limit exceeded: {max_concurrent_observed} > 2"

            # All jobs should eventually complete
            all_jobs = wish.job_manager.get_all_jobs()
            completed = sum(1 for job in all_jobs.values()
                          if job.status == "completed")
            assert completed >= 1  # At least some jobs completed

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_job_output_aggregation_workflow(self):
        """Test aggregating outputs from multiple parallel jobs."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        session = await wish.start_session()

        try:
            # Execute parallel scans
            await session.send_prompt("scan 10.10.10.1, 10.10.10.2, and 10.10.10.3 and summarize all findings")

            # Wait for completion
            await asyncio.sleep(1.5)

            # Get aggregated results
            state = await session.get_state()

            # Should have results from multiple hosts
            assert len(state.hosts) >= 1

            # Collect all services across hosts
            all_services = []
            for host in state.hosts.values():
                all_services.extend(host.services)

            # Should have discovered services
            assert len(all_services) > 0

            # Check job outputs were preserved
            all_jobs = wish.job_manager.get_all_jobs()
            scan_jobs = [job for job in all_jobs.values()
                        if job.tool_name == "nmap" or (job.command and "nmap" in job.command)]

            # Each scan job should have output
            for job in scan_jobs:
                assert job.full_output is not None
                assert len(job.full_output) > 0

            # Ask for summary
            result = await session.send_prompt("summarize what was found across all targets")

            # Summary should mention multiple aspects
            summary = result.result.lower()
            assert any(word in summary for word in ["hosts", "services", "ports"])

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_scan_result_interpretation(self):
        """Test AI interpretation of scan results."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        session = await wish.start_session()

        try:
            # Perform scan
            await session.send_prompt("scan 10.10.10.3")

            # Ask for interpretation
            result = await session.send_prompt("analyze the scan results and identify potential vulnerabilities")

            # Should mention discovered services
            response_lower = result.result.lower()
            assert any(service in response_lower for service in ["ssh", "smb", "samba", "web"])

            # Should provide actionable insights
            assert any(action in response_lower for action in
                      ["enumerate", "check", "test", "exploit", "vulnerable"])

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_enhanced_parallel_scan_workflow(self):
        """Test enhanced parallel scanning with job management."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        # Track detailed job execution
        job_metrics = {
            "started": [],
            "completed": [],
            "max_concurrent": 0,
            "current_running": 0
        }

        @wish.on_event(EventType.JOB_STARTED)
        async def on_job_start(event):
            job_metrics["started"].append({
                "job_id": event.data.get("job_id"),
                "time": event.timestamp,
                "tool": event.data.get("tool")
            })
            job_metrics["current_running"] += 1
            job_metrics["max_concurrent"] = max(job_metrics["max_concurrent"],
                                               job_metrics["current_running"])

        @wish.on_event(EventType.JOB_COMPLETED)
        async def on_job_complete(event):
            job_metrics["completed"].append({
                "job_id": event.data.get("job_id"),
                "time": event.timestamp,
                "duration": event.data.get("duration")
            })
            job_metrics["current_running"] -= 1

        session = await wish.start_session()

        try:
            # Request parallel scans of multiple targets
            await session.send_prompt("scan these targets simultaneously: 10.10.10.1-5")

            # Wait for all jobs to complete
            await asyncio.sleep(1.5)

            # Verify parallel execution
            assert len(job_metrics["started"]) >= 3  # Multiple scans
            assert job_metrics["max_concurrent"] > 1  # Actual parallelism

            # Verify all jobs completed
            assert len(job_metrics["completed"]) == len(job_metrics["started"])

            # Check timing - jobs should overlap
            if len(job_metrics["started"]) >= 2:
                # Sort by start time
                sorted_starts = sorted(job_metrics["started"], key=lambda x: x["time"])
                sorted_completes = sorted(job_metrics["completed"], key=lambda x: x["time"])

                # First job should complete after second job starts (overlap)
                if len(sorted_starts) >= 2 and len(sorted_completes) >= 1:
                    first_complete = next((c for c in sorted_completes
                                         if c["job_id"] == sorted_starts[0]["job_id"]), None)
                    if first_complete:
                        assert sorted_starts[1]["time"] < first_complete["time"], \
                            "Jobs should execute in parallel"

            # Verify scan results
            state = await session.get_state()
            assert len(state.hosts) >= 1  # At least one host discovered

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_job_dependency_workflow(self):
        """Test workflows with job dependencies."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        # Track job execution order
        execution_order = []

        @wish.on_event(EventType.JOB_STARTED)
        async def track_execution(event):
            execution_order.append({
                "job_id": event.data.get("job_id"),
                "tool": event.data.get("tool"),
                "command": event.data.get("command")
            })

        session = await wish.start_session()

        try:
            # Execute workflow with natural dependencies
            await session.send_prompt("first scan 10.10.10.3, then enumerate the discovered services")

            # Wait for completion
            await asyncio.sleep(1.0)

            # Verify execution order
            assert len(execution_order) >= 2

            # Scan should come before enumeration
            scan_idx = next((i for i, job in enumerate(execution_order)
                           if "nmap" in str(job.get("tool", ""))), None)
            enum_idx = next((i for i, job in enumerate(execution_order)
                           if any(tool in str(job.get("tool", ""))
                                for tool in ["enum4linux", "gobuster", "nikto"])), None)

            if scan_idx is not None and enum_idx is not None:
                assert scan_idx < enum_idx, "Scan should execute before enumeration"

            # Verify state progression
            state = await session.get_state()
            assert len(state.hosts) > 0

            # Should have discovered services
            total_services = sum(len(h.services) for h in state.hosts.values())
            assert total_services > 0

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_concurrent_job_limit_workflow(self):
        """Test respecting concurrent job limits in workflows."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        # Set a low limit for testing
        wish.job_manager.max_concurrent_jobs = 2

        # Track concurrent execution
        concurrent_tracking = []

        @wish.on_event(EventType.JOB_STARTED)
        async def on_start(event):
            running = len(wish.job_manager.get_running_jobs())
            concurrent_tracking.append(("start", running))

        @wish.on_event(EventType.JOB_COMPLETED)
        async def on_complete(event):
            running = len(wish.job_manager.get_running_jobs())
            concurrent_tracking.append(("complete", running))

        session = await wish.start_session()

        try:
            # Submit many parallel tasks
            await session.send_prompt("scan the entire 10.10.10.0/24 subnet quickly")

            # Wait for processing
            await asyncio.sleep(2.0)

            # Verify limit was respected
            max_concurrent_observed = max((count for event, count in concurrent_tracking
                                         if event == "start"), default=0)
            assert max_concurrent_observed <= 2, \
                f"Concurrent limit exceeded: {max_concurrent_observed} > 2"

            # All jobs should eventually complete
            all_jobs = wish.job_manager.get_all_jobs()
            completed = sum(1 for job in all_jobs.values()
                          if job.status == "completed")
            assert completed >= 1  # At least some jobs completed

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_job_output_aggregation_workflow(self):
        """Test aggregating outputs from multiple parallel jobs."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        session = await wish.start_session()

        try:
            # Execute parallel scans
            await session.send_prompt("scan 10.10.10.1, 10.10.10.2, and 10.10.10.3 and summarize all findings")

            # Wait for completion
            await asyncio.sleep(1.5)

            # Get aggregated results
            state = await session.get_state()

            # Should have results from multiple hosts
            assert len(state.hosts) >= 1

            # Collect all services across hosts
            all_services = []
            for host in state.hosts.values():
                all_services.extend(host.services)

            # Should have discovered services
            assert len(all_services) > 0

            # Check job outputs were preserved
            all_jobs = wish.job_manager.get_all_jobs()
            scan_jobs = [job for job in all_jobs.values()
                        if job.tool_name == "nmap" or (job.command and "nmap" in job.command)]

            # Each scan job should have output
            for job in scan_jobs:
                assert job.full_output is not None
                assert len(job.full_output) > 0

            # Ask for summary
            result = await session.send_prompt("summarize what was found across all targets")

            # Summary should mention multiple aspects
            summary = result.result.lower()
            assert any(word in summary for word in ["hosts", "services", "ports"])

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_parallel_scan_workflow(self):
        """Test parallel scanning of multiple hosts."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        # Track job events
        job_events = []

        @wish.on_event(EventType.JOB_STARTED)
        async def on_job(event):
            job_events.append(event)

        session = await wish.start_session()

        try:
            # Request parallel scans
            await session.send_prompt("scan 10.10.10.1, 10.10.10.2, and 10.10.10.3 in parallel")

            # Multiple jobs should be started
            assert len(job_events) > 0

            # Wait for completion
            await asyncio.sleep(0.1)  # Give time for mock execution

            # All targets should be scanned
            state = await session.get_state()
            assert len(state.hosts) >= 1  # At least one successful scan

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_enhanced_parallel_scan_workflow(self):
        """Test enhanced parallel scanning with job management."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        # Track detailed job execution
        job_metrics = {
            "started": [],
            "completed": [],
            "max_concurrent": 0,
            "current_running": 0
        }

        @wish.on_event(EventType.JOB_STARTED)
        async def on_job_start(event):
            job_metrics["started"].append({
                "job_id": event.data.get("job_id"),
                "time": event.timestamp,
                "tool": event.data.get("tool")
            })
            job_metrics["current_running"] += 1
            job_metrics["max_concurrent"] = max(job_metrics["max_concurrent"],
                                               job_metrics["current_running"])

        @wish.on_event(EventType.JOB_COMPLETED)
        async def on_job_complete(event):
            job_metrics["completed"].append({
                "job_id": event.data.get("job_id"),
                "time": event.timestamp,
                "duration": event.data.get("duration")
            })
            job_metrics["current_running"] -= 1

        session = await wish.start_session()

        try:
            # Request parallel scans of multiple targets
            await session.send_prompt("scan these targets simultaneously: 10.10.10.1-5")

            # Wait for all jobs to complete
            await asyncio.sleep(1.5)

            # Verify parallel execution
            assert len(job_metrics["started"]) >= 3  # Multiple scans
            assert job_metrics["max_concurrent"] > 1  # Actual parallelism

            # Verify all jobs completed
            assert len(job_metrics["completed"]) == len(job_metrics["started"])

            # Check timing - jobs should overlap
            if len(job_metrics["started"]) >= 2:
                # Sort by start time
                sorted_starts = sorted(job_metrics["started"], key=lambda x: x["time"])
                sorted_completes = sorted(job_metrics["completed"], key=lambda x: x["time"])

                # First job should complete after second job starts (overlap)
                if len(sorted_starts) >= 2 and len(sorted_completes) >= 1:
                    first_complete = next((c for c in sorted_completes
                                         if c["job_id"] == sorted_starts[0]["job_id"]), None)
                    if first_complete:
                        assert sorted_starts[1]["time"] < first_complete["time"], \
                            "Jobs should execute in parallel"

            # Verify scan results
            state = await session.get_state()
            assert len(state.hosts) >= 1  # At least one host discovered

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_job_dependency_workflow(self):
        """Test workflows with job dependencies."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        # Track job execution order
        execution_order = []

        @wish.on_event(EventType.JOB_STARTED)
        async def track_execution(event):
            execution_order.append({
                "job_id": event.data.get("job_id"),
                "tool": event.data.get("tool"),
                "command": event.data.get("command")
            })

        session = await wish.start_session()

        try:
            # Execute workflow with natural dependencies
            await session.send_prompt("first scan 10.10.10.3, then enumerate the discovered services")

            # Wait for completion
            await asyncio.sleep(1.0)

            # Verify execution order
            assert len(execution_order) >= 2

            # Scan should come before enumeration
            scan_idx = next((i for i, job in enumerate(execution_order)
                           if "nmap" in str(job.get("tool", ""))), None)
            enum_idx = next((i for i, job in enumerate(execution_order)
                           if any(tool in str(job.get("tool", ""))
                                for tool in ["enum4linux", "gobuster", "nikto"])), None)

            if scan_idx is not None and enum_idx is not None:
                assert scan_idx < enum_idx, "Scan should execute before enumeration"

            # Verify state progression
            state = await session.get_state()
            assert len(state.hosts) > 0

            # Should have discovered services
            total_services = sum(len(h.services) for h in state.hosts.values())
            assert total_services > 0

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_concurrent_job_limit_workflow(self):
        """Test respecting concurrent job limits in workflows."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        # Set a low limit for testing
        wish.job_manager.max_concurrent_jobs = 2

        # Track concurrent execution
        concurrent_tracking = []

        @wish.on_event(EventType.JOB_STARTED)
        async def on_start(event):
            running = len(wish.job_manager.get_running_jobs())
            concurrent_tracking.append(("start", running))

        @wish.on_event(EventType.JOB_COMPLETED)
        async def on_complete(event):
            running = len(wish.job_manager.get_running_jobs())
            concurrent_tracking.append(("complete", running))

        session = await wish.start_session()

        try:
            # Submit many parallel tasks
            await session.send_prompt("scan the entire 10.10.10.0/24 subnet quickly")

            # Wait for processing
            await asyncio.sleep(2.0)

            # Verify limit was respected
            max_concurrent_observed = max((count for event, count in concurrent_tracking
                                         if event == "start"), default=0)
            assert max_concurrent_observed <= 2, \
                f"Concurrent limit exceeded: {max_concurrent_observed} > 2"

            # All jobs should eventually complete
            all_jobs = wish.job_manager.get_all_jobs()
            completed = sum(1 for job in all_jobs.values()
                          if job.status == "completed")
            assert completed >= 1  # At least some jobs completed

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_job_output_aggregation_workflow(self):
        """Test aggregating outputs from multiple parallel jobs."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        session = await wish.start_session()

        try:
            # Execute parallel scans
            await session.send_prompt("scan 10.10.10.1, 10.10.10.2, and 10.10.10.3 and summarize all findings")

            # Wait for completion
            await asyncio.sleep(1.5)

            # Get aggregated results
            state = await session.get_state()

            # Should have results from multiple hosts
            assert len(state.hosts) >= 1

            # Collect all services across hosts
            all_services = []
            for host in state.hosts.values():
                all_services.extend(host.services)

            # Should have discovered services
            assert len(all_services) > 0

            # Check job outputs were preserved
            all_jobs = wish.job_manager.get_all_jobs()
            scan_jobs = [job for job in all_jobs.values()
                        if job.tool_name == "nmap" or (job.command and "nmap" in job.command)]

            # Each scan job should have output
            for job in scan_jobs:
                assert job.full_output is not None
                assert len(job.full_output) > 0

            # Ask for summary
            result = await session.send_prompt("summarize what was found across all targets")

            # Summary should mention multiple aspects
            summary = result.result.lower()
            assert any(word in summary for word in ["hosts", "services", "ports"])

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_scan_to_finding_workflow(self):
        """Test workflow from scan to vulnerability finding."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        session = await wish.start_session()

        try:
            # Scan known vulnerable target
            await session.send_prompt(f"scan {HTB_LAME_SCENARIO['target']}")

            # Check for vulnerabilities
            await session.send_prompt("check the discovered services for known vulnerabilities")

            # Should have findings
            state = await session.get_state()
            assert len(state.findings) > 0

            # Check finding details
            finding = next(iter(state.findings.values()))
            assert finding.severity in ["critical", "high", "medium", "low"]
            assert finding.category == "vulnerability"

            # Ask for exploitation advice
            result = await session.send_prompt("how can I exploit the vulnerabilities found?")

            # Should mention specific vulnerability
            assert HTB_LAME_SCENARIO["vulnerability"] in result.result or "samba" in result.result.lower()

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_enhanced_parallel_scan_workflow(self):
        """Test enhanced parallel scanning with job management."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        # Track detailed job execution
        job_metrics = {
            "started": [],
            "completed": [],
            "max_concurrent": 0,
            "current_running": 0
        }

        @wish.on_event(EventType.JOB_STARTED)
        async def on_job_start(event):
            job_metrics["started"].append({
                "job_id": event.data.get("job_id"),
                "time": event.timestamp,
                "tool": event.data.get("tool")
            })
            job_metrics["current_running"] += 1
            job_metrics["max_concurrent"] = max(job_metrics["max_concurrent"],
                                               job_metrics["current_running"])

        @wish.on_event(EventType.JOB_COMPLETED)
        async def on_job_complete(event):
            job_metrics["completed"].append({
                "job_id": event.data.get("job_id"),
                "time": event.timestamp,
                "duration": event.data.get("duration")
            })
            job_metrics["current_running"] -= 1

        session = await wish.start_session()

        try:
            # Request parallel scans of multiple targets
            await session.send_prompt("scan these targets simultaneously: 10.10.10.1-5")

            # Wait for all jobs to complete
            await asyncio.sleep(1.5)

            # Verify parallel execution
            assert len(job_metrics["started"]) >= 3  # Multiple scans
            assert job_metrics["max_concurrent"] > 1  # Actual parallelism

            # Verify all jobs completed
            assert len(job_metrics["completed"]) == len(job_metrics["started"])

            # Check timing - jobs should overlap
            if len(job_metrics["started"]) >= 2:
                # Sort by start time
                sorted_starts = sorted(job_metrics["started"], key=lambda x: x["time"])
                sorted_completes = sorted(job_metrics["completed"], key=lambda x: x["time"])

                # First job should complete after second job starts (overlap)
                if len(sorted_starts) >= 2 and len(sorted_completes) >= 1:
                    first_complete = next((c for c in sorted_completes
                                         if c["job_id"] == sorted_starts[0]["job_id"]), None)
                    if first_complete:
                        assert sorted_starts[1]["time"] < first_complete["time"], \
                            "Jobs should execute in parallel"

            # Verify scan results
            state = await session.get_state()
            assert len(state.hosts) >= 1  # At least one host discovered

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_job_dependency_workflow(self):
        """Test workflows with job dependencies."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        # Track job execution order
        execution_order = []

        @wish.on_event(EventType.JOB_STARTED)
        async def track_execution(event):
            execution_order.append({
                "job_id": event.data.get("job_id"),
                "tool": event.data.get("tool"),
                "command": event.data.get("command")
            })

        session = await wish.start_session()

        try:
            # Execute workflow with natural dependencies
            await session.send_prompt("first scan 10.10.10.3, then enumerate the discovered services")

            # Wait for completion
            await asyncio.sleep(1.0)

            # Verify execution order
            assert len(execution_order) >= 2

            # Scan should come before enumeration
            scan_idx = next((i for i, job in enumerate(execution_order)
                           if "nmap" in str(job.get("tool", ""))), None)
            enum_idx = next((i for i, job in enumerate(execution_order)
                           if any(tool in str(job.get("tool", ""))
                                for tool in ["enum4linux", "gobuster", "nikto"])), None)

            if scan_idx is not None and enum_idx is not None:
                assert scan_idx < enum_idx, "Scan should execute before enumeration"

            # Verify state progression
            state = await session.get_state()
            assert len(state.hosts) > 0

            # Should have discovered services
            total_services = sum(len(h.services) for h in state.hosts.values())
            assert total_services > 0

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_concurrent_job_limit_workflow(self):
        """Test respecting concurrent job limits in workflows."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        # Set a low limit for testing
        wish.job_manager.max_concurrent_jobs = 2

        # Track concurrent execution
        concurrent_tracking = []

        @wish.on_event(EventType.JOB_STARTED)
        async def on_start(event):
            running = len(wish.job_manager.get_running_jobs())
            concurrent_tracking.append(("start", running))

        @wish.on_event(EventType.JOB_COMPLETED)
        async def on_complete(event):
            running = len(wish.job_manager.get_running_jobs())
            concurrent_tracking.append(("complete", running))

        session = await wish.start_session()

        try:
            # Submit many parallel tasks
            await session.send_prompt("scan the entire 10.10.10.0/24 subnet quickly")

            # Wait for processing
            await asyncio.sleep(2.0)

            # Verify limit was respected
            max_concurrent_observed = max((count for event, count in concurrent_tracking
                                         if event == "start"), default=0)
            assert max_concurrent_observed <= 2, \
                f"Concurrent limit exceeded: {max_concurrent_observed} > 2"

            # All jobs should eventually complete
            all_jobs = wish.job_manager.get_all_jobs()
            completed = sum(1 for job in all_jobs.values()
                          if job.status == "completed")
            assert completed >= 1  # At least some jobs completed

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_job_output_aggregation_workflow(self):
        """Test aggregating outputs from multiple parallel jobs."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        session = await wish.start_session()

        try:
            # Execute parallel scans
            await session.send_prompt("scan 10.10.10.1, 10.10.10.2, and 10.10.10.3 and summarize all findings")

            # Wait for completion
            await asyncio.sleep(1.5)

            # Get aggregated results
            state = await session.get_state()

            # Should have results from multiple hosts
            assert len(state.hosts) >= 1

            # Collect all services across hosts
            all_services = []
            for host in state.hosts.values():
                all_services.extend(host.services)

            # Should have discovered services
            assert len(all_services) > 0

            # Check job outputs were preserved
            all_jobs = wish.job_manager.get_all_jobs()
            scan_jobs = [job for job in all_jobs.values()
                        if job.tool_name == "nmap" or (job.command and "nmap" in job.command)]

            # Each scan job should have output
            for job in scan_jobs:
                assert job.full_output is not None
                assert len(job.full_output) > 0

            # Ask for summary
            result = await session.send_prompt("summarize what was found across all targets")

            # Summary should mention multiple aspects
            summary = result.result.lower()
            assert any(word in summary for word in ["hosts", "services", "ports"])

        finally:
            await session.end()
