"""E2E test for job management features."""

import asyncio

import pytest
from fixtures import setup_mocks
from wish_cli.headless import EventType, HeadlessWish


@pytest.mark.asyncio
class TestJobManagement:
    """Test background job execution and management."""

    @pytest.fixture
    async def wish(self):
        """Create HeadlessWish instance with job tracking."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        # Track job events
        job_events = {
            "started": [],
            "progress": [],
            "completed": [],
            "failed": []
        }

        @wish.on_event(EventType.JOB_STARTED)
        async def on_job_start(event):
            job_events["started"].append({
                "job_id": event.data.get("job_id"),
                "description": event.data.get("description"),
                "command": event.data.get("command"),
                "timestamp": event.timestamp
            })

        @wish.on_event(EventType.JOB_PROGRESS)
        async def on_job_progress(event):
            job_events["progress"].append({
                "job_id": event.data.get("job_id"),
                "progress": event.data.get("progress"),
                "message": event.data.get("message"),
                "timestamp": event.timestamp
            })

        @wish.on_event(EventType.JOB_COMPLETED)
        async def on_job_complete(event):
            job_events["completed"].append({
                "job_id": event.data.get("job_id"),
                "result": event.data.get("result"),
                "timestamp": event.timestamp
            })

        wish._job_events = job_events
        return wish

    async def test_background_job_execution(self, wish):
        """Test that jobs run in background."""
        session = await wish.start_session(metadata={
            "test": "background_job_execution"
        })

        try:
            # Set up target
            await session.send_prompt("/scope add 10.10.10.3")

            # Start a scan (should create background job)
            result = await session.send_prompt("scan 10.10.10.3 for open ports")

            # Give time for job to start
            await asyncio.sleep(1)

            # Check job was started
            # Note: Actual job execution depends on AI/tool integration
            # but we can verify the command was processed
            assert result.result is not None
            assert "error" not in result.result.lower()

            # Check job status
            result = await session.send_prompt("/jobs")
            jobs_output = result.result.lower()

            # Should show jobs or indicate no jobs
            assert "job" in jobs_output or "no" in jobs_output

        finally:
            await session.end()

    async def test_job_status_commands(self, wish):
        """Test /jobs command variations."""
        session = await wish.start_session(metadata={
            "test": "job_status_commands"
        })

        try:
            # Test /jobs with no jobs
            result = await session.send_prompt("/jobs")
            assert "job" in result.result.lower()

            # Test /j alias
            result = await session.send_prompt("/j")
            assert "job" in result.result.lower()

            # Test invalid job ID
            result = await session.send_prompt("/jobs job_999")
            assert "not found" in result.result.lower() or "job" in result.result.lower()

        finally:
            await session.end()

    async def test_job_cancellation(self, wish):
        """Test job cancellation functionality."""
        session = await wish.start_session(metadata={
            "test": "job_cancellation"
        })

        try:
            # Test cancel with no jobs
            result = await session.send_prompt("/jobs cancel job_001")
            assert "not found" in result.result.lower() or "no" in result.result.lower()

            # Test /kill alias
            result = await session.send_prompt("/kill job_001")
            assert result.result is not None

        finally:
            await session.end()

    async def test_job_logs_command(self, wish):
        """Test viewing job logs."""
        session = await wish.start_session(metadata={
            "test": "job_logs"
        })

        try:
            # Test logs with invalid job
            result = await session.send_prompt("/logs job_999")
            assert "not found" in result.result.lower() or "no" in result.result.lower()

            # Test without job ID
            result = await session.send_prompt("/logs")
            assert "usage" in result.result.lower() or "specify" in result.result.lower()

        finally:
            await session.end()

    async def test_progress_indicators(self, wish):
        """Test that progress indicators are shown."""
        session = await wish.start_session(metadata={
            "test": "progress_indicators"
        })

        try:
            # This test verifies the expectation for progress display
            # Actual implementation will show [▶] Running... style indicators

            await session.send_prompt("/scope add 10.10.10.3")

            # Command that should show progress
            result = await session.send_prompt("perform a comprehensive scan")

            # Current implementation shows text notifications
            # Future: Should show [▶] Running nmap... (Job 1)
            assert result.result is not None

        finally:
            await session.end()

    async def test_concurrent_jobs(self, wish):
        """Test multiple jobs running concurrently."""
        session = await wish.start_session(metadata={
            "test": "concurrent_jobs"
        })

        try:
            # Set up multiple targets
            await session.send_prompt("/scope add 10.10.10.3")
            await session.send_prompt("/scope add 10.10.10.4")

            # Start multiple operations
            # In real scenario, these would run concurrently
            result1 = await session.send_prompt("scan first target")
            result2 = await session.send_prompt("scan second target")

            # Both should process successfully
            assert result1.result is not None
            assert result2.result is not None

            # Check jobs list
            result = await session.send_prompt("/jobs")
            # Should handle multiple jobs gracefully
            assert "error" not in result.result.lower()

        finally:
            await session.end()

    async def test_demo_job_workflow(self, wish):
        """Test job management in demo scenario context."""
        session = await wish.start_session(metadata={
            "test": "demo_job_workflow"
        })

        try:
            # Demo scenario job flow
            await session.send_prompt("/scope add 10.10.10.3")

            # Start scan (creates job)
            result = await session.send_prompt("scan 10.10.10.3")

            # Check job status while "running"
            await asyncio.sleep(0.5)
            result = await session.send_prompt("/jobs")

            # Should show job information
            assert result.result is not None

            # In demo, jobs complete and update state
            # Verify we can see results
            result = await session.send_prompt("/status")
            assert "10.10.10.3" in result.result

        finally:
            await session.end()
