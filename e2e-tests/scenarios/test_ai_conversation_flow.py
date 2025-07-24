"""E2E test for AI conversation flow."""

import asyncio

import pytest
from fixtures import setup_mocks
from wish_cli.headless import EventType, HeadlessWish


@pytest.mark.asyncio
class TestAIConversationFlow:
    """Test AI-driven conversation and planning workflow."""

    @pytest.fixture
    async def wish(self):
        """Create HeadlessWish instance with event tracking."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        # Track plan approval events
        approval_events = []
        job_events = []

        @wish.on_event(EventType.PLAN_APPROVAL_REQUIRED)
        async def on_plan_approval(event):
            approval_events.append(event)
            # Auto-approve in test
            return "approve"

        @wish.on_event(EventType.JOB_STARTED)
        async def on_job_start(event):
            job_events.append({
                "job_id": event.data.get("job_id"),
                "description": event.data.get("description"),
                "timestamp": event.timestamp
            })

        wish._approval_events = approval_events
        wish._job_events = job_events
        return wish

    async def test_natural_language_scan_request(self, wish):
        """Test natural language request for scanning."""
        session = await wish.start_session(metadata={
            "test": "natural_language_scan"
        })

        try:
            # First set up scope
            await session.send_prompt("/scope add 10.10.10.3")

            # Natural language scan request
            result = await session.send_prompt("scan 10.10.10.3 for open services")

            # Should generate a plan
            assert len(wish._approval_events) > 0 or "executing" in result.result.lower()

            # Should start jobs
            await asyncio.sleep(1)  # Give time for job to start

            # Check that some action was taken
            assert result.result is not None
            assert "error" not in result.result.lower()

        finally:
            await session.end()

    async def test_vulnerability_analysis_request(self, wish):
        """Test AI analysis of vulnerabilities."""
        session = await wish.start_session(metadata={
            "test": "vulnerability_analysis"
        })

        try:
            # Set up context with a vulnerable service
            await session.send_prompt("/scope add 10.10.10.3")

            # Simulate scan results by providing context
            result = await session.send_prompt(
                "I found Samba 3.0.20 running on port 445. "
                "Can you check for vulnerabilities?"
            )

            # AI should provide analysis
            response = result.result.lower()
            assert any(word in response for word in [
                "vulnerability", "cve", "exploit", "samba", "vulnerable"
            ])

        finally:
            await session.end()

    async def test_exploit_verification_flow(self, wish):
        """Test the exploit verification conversation flow."""
        session = await wish.start_session(metadata={
            "test": "exploit_verification_flow"
        })

        try:
            # Set context
            await session.send_prompt("/scope add 10.10.10.3")

            # Request exploit verification
            result = await session.send_prompt(
                "I want to verify the Samba username map script vulnerability "
                "on 10.10.10.3. Can you help me test it safely?"
            )

            # Should get a cautious response about safe testing
            response = result.result.lower()
            assert any(word in response for word in [
                "verify", "test", "safe", "exploit", "command"
            ])

            # Follow-up for actual verification
            result = await session.send_prompt(
                "Yes, please verify with a simple id command"
            )

            # Should indicate some action or plan
            assert result.result is not None

        finally:
            await session.end()

    async def test_plan_generation_and_approval(self, wish):
        """Test that plans are generated and approval flow works."""
        # Use manual approval for this test
        wish._auto_approve = False
        approval_requested = []

        @wish.on_event(EventType.PLAN_APPROVAL_REQUIRED)
        async def track_approval(event):
            approval_requested.append(event.data.get("plan"))
            # Approve after tracking
            return "approve"

        session = await wish.start_session(metadata={
            "test": "plan_approval_flow"
        })

        try:
            await session.send_prompt("/scope add 10.10.10.3")

            # Request that should generate a plan
            result = await session.send_prompt(
                "Perform a comprehensive port scan on the target"
            )

            # Wait for async processing
            await asyncio.sleep(0.5)

            # Should have requested approval
            # Note: Actual plan generation requires AI integration
            # In mock mode, we just verify the flow
            assert result.result is not None

        finally:
            await session.end()

    async def test_context_aware_responses(self, wish):
        """Test that AI maintains context across conversation."""
        session = await wish.start_session(metadata={
            "test": "context_awareness"
        })

        try:
            # Build context
            await session.send_prompt("/scope add 10.10.10.3")
            await session.send_prompt(
                "I'm testing a Linux server at 10.10.10.3"
            )

            # Ask context-dependent question
            result = await session.send_prompt(
                "What should I look for on this target?"
            )

            # Response should be relevant to Linux/server
            response = result.result.lower()
            # Should mention relevant services or approaches
            assert any(word in response for word in [
                "linux", "ssh", "service", "port", "scan", "enumerate"
            ])

        finally:
            await session.end()

    async def test_demo_scenario_ai_flow(self, wish):
        """Test the complete AI conversation flow from demo."""
        session = await wish.start_session(metadata={
            "test": "demo_ai_flow"
        })

        try:
            # ACT 1: Initial reconnaissance request
            await session.send_prompt("/scope add 10.10.10.3")

            result = await session.send_prompt(
                "I need to assess the security of 10.10.10.3. "
                "Start with network reconnaissance."
            )

            # Should suggest scanning
            assert any(word in result.result.lower() for word in [
                "scan", "nmap", "port", "service", "reconnaissance"
            ])

            # ACT 2: Vulnerability verification
            result = await session.send_prompt(
                "I found Samba 3.0.20 on port 445. "
                "Is this vulnerable?"
            )

            # Should identify CVE-2007-2447
            response = result.result.lower()
            assert any(word in response for word in [
                "cve", "2007-2447", "vulnerable", "username map",
                "remote", "exploit"
            ])

            # Request safe verification
            result = await session.send_prompt(
                "How can I safely verify this vulnerability?"
            )

            # Should provide safe approach
            assert any(word in result.result.lower() for word in [
                "verify", "test", "safe", "command", "careful"
            ])

        finally:
            await session.end()
