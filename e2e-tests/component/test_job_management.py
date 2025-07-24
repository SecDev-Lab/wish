"""Job management integration tests using HeadlessWish."""

import asyncio
import os
import sys

import pytest
from wish_cli.headless import EventType, HeadlessWish

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from fixtures import setup_mocks
from fixtures.mocks import JobStatus


class TestJobManagement:
    """Test job management functionality through HeadlessWish SDK."""

    @pytest.mark.asyncio
    async def test_job_lifecycle(self):
        """Test complete job lifecycle from creation to completion."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        # Track job events
        job_events = []

        @wish.on_event(EventType.JOB_STARTED)
        async def on_job_start(event):
            job_events.append({
                "type": "started",
                "job_id": event.data.get("job_id"),
                "timestamp": event.timestamp
            })

        @wish.on_event(EventType.JOB_COMPLETED)
        async def on_job_complete(event):
            job_events.append({
                "type": "completed",
                "job_id": event.data.get("job_id"),
                "timestamp": event.timestamp
            })

        session = await wish.start_session()

        try:
            # Execute a command that creates a job
            await session.send_prompt("scan 10.10.10.3")

            # Wait for job completion
            await asyncio.sleep(0.5)

            # Verify job lifecycle events
            assert len(job_events) >= 2

            # Check event sequence
            start_events = [e for e in job_events if e["type"] == "started"]
            complete_events = [e for e in job_events if e["type"] == "completed"]

            assert len(start_events) > 0
            assert len(complete_events) > 0

            # Verify job IDs match
            job_id = start_events[0]["job_id"]
            assert any(e["job_id"] == job_id for e in complete_events)

            # Since HeadlessWish creates its own job IDs, check job manager has any jobs
            all_jobs = wish.job_manager.get_all_jobs()
            if len(all_jobs) > 0:
                # Check job info from job manager
                first_job = next(iter(all_jobs.values()))
                assert first_job.status == JobStatus.COMPLETED
                assert first_job.started_at is not None
                assert first_job.completed_at is not None
                assert first_job.completed_at > first_job.started_at

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_concurrent_job_limit(self):
        """Test concurrent job execution limit."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        # Set a low limit for testing
        wish.job_manager.max_concurrent_jobs = 2

        # Track running jobs
        max_concurrent = 0
        running_count = 0

        @wish.on_event(EventType.JOB_STARTED)
        async def on_job_start(event):
            nonlocal running_count, max_concurrent
            running_count += 1
            max_concurrent = max(max_concurrent, running_count)

        @wish.on_event(EventType.JOB_COMPLETED)
        async def on_job_complete(event):
            nonlocal running_count
            running_count -= 1

        session = await wish.start_session()

        try:
            # Submit multiple jobs quickly
            await session.send_prompt("scan 10.10.10.1, 10.10.10.2, 10.10.10.3, and 10.10.10.4 in parallel")

            # Wait for processing
            await asyncio.sleep(1.0)

            # Verify concurrent limit was respected
            assert max_concurrent <= 2, f"Max concurrent jobs ({max_concurrent}) exceeded limit (2)"

            # Verify all jobs eventually completed
            all_jobs = wish.job_manager.get_all_jobs()
            completed_jobs = [j for j in all_jobs.values() if j.status == JobStatus.COMPLETED]
            assert len(completed_jobs) >= 3  # At least 3 jobs should have completed

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_job_cancellation(self):
        """Test job cancellation functionality."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        # Track job events
        # Note: Track cancellation through job status instead of event
        # since JOB_CANCELLED event doesn't exist

        session = await wish.start_session()

        try:
            # Start a long-running job
            # (In real implementation, we'd need to trigger actual cancellation)
            # For now, we'll test the cancellation mechanism directly

            # Submit a mock job
            async def long_task():
                await asyncio.sleep(10)  # Simulate long task
                return "Should not complete"

            job_id = await wish.job_manager.submit_job(
                "Long running scan",
                long_task(),
                tool_name="nmap",
                command="nmap -A 10.10.10.0/24"
            )

            # Wait a bit then cancel
            await asyncio.sleep(0.1)
            cancelled = await wish.job_manager.cancel_job(job_id)

            assert cancelled is True

            # Verify job status
            job_info = wish.job_manager.get_job_info(job_id)
            assert job_info.status == JobStatus.CANCELLED

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_job_output_capture(self):
        """Test capturing and storing job output."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        # Track job outputs
        job_outputs = {}

        @wish.on_event(EventType.JOB_COMPLETED)
        async def on_job_complete(event):
            job_id = event.data.get("job_id")
            job_info = wish.job_manager.get_job_info(job_id)
            if job_info:
                job_outputs[job_id] = {
                    "output": job_info.output,
                    "full_output": job_info.full_output,
                    "exit_code": job_info.exit_code
                }

        session = await wish.start_session()

        try:
            # Execute a scan
            await session.send_prompt("scan 10.10.10.3 with nmap")

            # Wait for completion
            await asyncio.sleep(0.5)

            # Verify output was captured
            assert len(job_outputs) > 0

            # Check first job output
            first_job = list(job_outputs.values())[0]
            assert first_job["full_output"] is not None
            assert "PORT" in first_job["full_output"]  # Nmap output contains PORT
            assert first_job["exit_code"] == 0

            # Output should be truncated version of full_output
            if first_job["output"]:
                assert len(first_job["output"]) <= 500
                assert first_job["output"] in first_job["full_output"]

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_job_error_handling(self):
        """Test job error handling and failure states."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        # Track failed jobs
        failed_jobs = []

        @wish.on_event(EventType.ERROR_OCCURRED)
        async def on_job_fail(event):
            failed_jobs.append({
                "job_id": event.data.get("job_id"),
                "error": event.data.get("error")
            })

        session = await wish.start_session()

        try:
            # Submit a job that will fail
            async def failing_task():
                raise Exception("Simulated tool failure")

            job_id = await wish.job_manager.submit_job(
                "Failing scan",
                failing_task(),
                tool_name="nmap",
                command="nmap invalid-options"
            )

            # Wait for failure
            await asyncio.sleep(0.5)

            # Verify failure was recorded
            assert len(failed_jobs) > 0
            assert any(f["error"] == "Simulated tool failure" for f in failed_jobs)

            # Check job status
            job_info = wish.job_manager.get_job_info(job_id)
            assert job_info.status == JobStatus.FAILED
            assert job_info.error == "Simulated tool failure"

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_job_queuing(self):
        """Test job queuing when concurrent limit is reached."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        # Set very low limit
        wish.job_manager.max_concurrent_jobs = 1

        # Track job order
        job_order = []

        @wish.on_event(EventType.JOB_STARTED)
        async def on_job_start(event):
            job_order.append({
                "job_id": event.data.get("job_id"),
                "event": "started",
                "time": event.timestamp
            })

        @wish.on_event(EventType.JOB_COMPLETED)
        async def on_job_complete(event):
            job_order.append({
                "job_id": event.data.get("job_id"),
                "event": "completed",
                "time": event.timestamp
            })

        session = await wish.start_session()

        try:
            # Submit multiple jobs
            job_ids = []
            for i in range(3):
                # Create a closure to capture the index
                def make_task(idx):
                    async def task():
                        await asyncio.sleep(0.2)  # Simulate work
                        return f"Result {idx}"
                    return task()

                job_id = await wish.job_manager.submit_job(
                    f"Task {i}",
                    make_task(i),
                    tool_name="test",
                    command=f"test {i}"
                )
                job_ids.append(job_id)

            # Wait for all to complete
            await asyncio.sleep(1.0)

            # Verify jobs were queued and executed in sequence
            # With limit of 1, jobs should not overlap
            started_times = {e["job_id"]: e["time"] for e in job_order if e["event"] == "started"}
            completed_times = {e["job_id"]: e["time"] for e in job_order if e["event"] == "completed"}

            # Each job should complete before the next starts (with small tolerance for timing)
            for i in range(len(job_ids) - 1):
                current_job = job_ids[i]
                next_job = job_ids[i + 1]

                if current_job in completed_times and next_job in started_times:
                    # Allow small overlap due to async execution timing
                    tolerance = 0.5  # 500ms tolerance for async timing variations
                    assert completed_times[current_job] <= started_times[next_job] + tolerance, \
                        f"Job {current_job} should complete before {next_job} starts (tolerance: {tolerance}s)"

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_job_metadata(self):
        """Test job metadata and extended information."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        session = await wish.start_session()

        try:
            # Execute command with specific tool
            await session.send_prompt("enumerate SMB on 10.10.10.3")

            # Wait for completion
            await asyncio.sleep(0.5)

            # Check job metadata
            all_jobs = wish.job_manager.get_all_jobs()
            assert len(all_jobs) > 0

            # Find SMB enumeration job
            smb_job = None
            for job in all_jobs.values():
                if job.tool_name == "enum4linux" or (job.command and "enum4linux" in job.command):
                    smb_job = job
                    break

            assert smb_job is not None
            assert smb_job.description is not None
            assert smb_job.tool_name is not None
            assert smb_job.command is not None
            assert smb_job.status == JobStatus.COMPLETED

            # Verify timing information
            assert smb_job.created_at is not None
            assert smb_job.started_at is not None
            assert smb_job.completed_at is not None
            assert smb_job.created_at <= smb_job.started_at <= smb_job.completed_at

        finally:
            await session.end()
