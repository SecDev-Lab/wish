"""AI and Knowledge integration tests using HeadlessWish."""

import os
import sys

import pytest
from wish_cli.headless import EventType, HeadlessWish

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import re

from fixtures import DANGEROUS_PATTERNS, MockEventCollector, setup_mocks


class TestAIIntegration:
    """Test AI components through HeadlessWish SDK."""

    @pytest.mark.asyncio
    async def test_plan_generation_basic(self):
        """Test basic plan generation for common tasks."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        # Collect plan approvals
        collector = MockEventCollector()

        @wish.on_event(EventType.PLAN_APPROVAL_REQUIRED)
        async def collect_plans(event):
            collector.collect_plan_approval(event)
            return "approve"

        session = await wish.start_session()

        try:
            # Test scan plan generation
            await session.send_prompt("scan 10.10.10.3 for open ports")

            # Plan should be generated and approved
            assert len(collector.plan_approvals) > 0
            plan = collector.plan_approvals[0]

            # Verify plan structure
            assert plan.description is not None
            assert len(plan.steps) > 0
            assert plan.rationale is not None

            # Verify scan plan specifics
            nmap_step = next((s for s in plan.steps if s.tool_name == "nmap"), None)
            assert nmap_step is not None
            assert "10.10.10.3" in nmap_step.command
            assert nmap_step.purpose is not None
            assert nmap_step.expected_result is not None

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_context_aware_planning(self):
        """Test that AI considers current state when planning."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        collector = MockEventCollector()

        @wish.on_event(EventType.PLAN_APPROVAL_REQUIRED)
        async def collect_plans(event):
            collector.collect_plan_approval(event)
            return "approve"

        session = await wish.start_session()

        try:
            # First set context by scanning
            await session.send_prompt("scan 10.10.10.3")

            # Clear previous plans
            collector.clear()

            # Now ask for enumeration - should be context-aware
            await session.send_prompt("enumerate the discovered SMB services")

            # Check generated plan
            assert len(collector.plan_approvals) > 0
            enum_plan = collector.plan_approvals[0]

            # Should include SMB-specific tools
            tool_names = [step.tool_name for step in enum_plan.steps]
            assert any(tool in tool_names for tool in ["enum4linux", "smbclient", "rpcclient"])

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_multi_step_planning(self):
        """Test generation of multi-step plans."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        collector = MockEventCollector()

        @wish.on_event(EventType.PLAN_APPROVAL_REQUIRED)
        async def collect_plans(event):
            collector.collect_plan_approval(event)
            return "approve"

        session = await wish.start_session()

        try:
            # Request comprehensive enumeration
            await session.send_prompt("perform comprehensive enumeration of web and SMB services")

            # Should generate multi-step plan
            assert len(collector.plan_approvals) > 0
            plan = collector.plan_approvals[0]

            # Should have multiple steps
            assert len(plan.steps) >= 2

            # Should cover different services
            tools_used = {step.tool_name for step in plan.steps}
            assert len(tools_used) >= 2  # Multiple different tools

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_knowledge_integration(self):
        """Test AI integration with knowledge base (HackTricks)."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        session = await wish.start_session()

        try:
            # Ask knowledge-based question
            result = await session.send_prompt("how to enumerate SMB shares on Linux?")

            # Response should include specific tools/techniques
            response_lower = result.result.lower()

            # Check for SMB enumeration tools mentioned
            expected_tools = ["smbclient", "enum4linux", "rpcclient", "smbmap"]
            found_tools = [tool for tool in expected_tools if tool in response_lower]
            assert len(found_tools) > 0, f"Expected SMB tools in response, got: {result.result}"

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_conversational_continuity(self):
        """Test AI maintains conversation context."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        session = await wish.start_session()

        try:
            # Set context
            await session.send_prompt("I found a Samba service on port 445")

            # Follow-up should understand context
            result = await session.send_prompt("what should I do next?")

            # Response should be relevant to SMB/Samba
            response_lower = result.result.lower()
            assert any(keyword in response_lower for keyword in
                      ["enumerate", "smb", "samba", "shares", "version"])

            # Further follow-up
            result = await session.send_prompt("can you be more specific?")

            # Should maintain context
            assert result.result is not None
            assert len(result.result) > 0

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_plan_approval_flow(self):
        """Test manual plan approval workflow."""
        wish = HeadlessWish(auto_approve=False)  # Manual approval
        wish = setup_mocks(wish)

        approved_count = 0
        rejected_count = 0

        @wish.on_event(EventType.PLAN_APPROVAL_REQUIRED)
        async def handle_approval(event):
            nonlocal approved_count, rejected_count
            from fixtures.mocks import get_plan_from_event
            plan = get_plan_from_event(event)

            # Approve scan plans, reject others
            if any("scan" in step.purpose.lower() for step in plan.steps):
                approved_count += 1
                return "approve"
            else:
                rejected_count += 1
                return "reject"

        session = await wish.start_session()

        try:
            # This should be approved
            result1 = await session.send_prompt("scan the network")
            assert result1.result is not None

            # This should be rejected
            result2 = await session.send_prompt("delete system files")
            # Even rejected plans should return a result (explaining rejection)
            assert result2.result is not None

            assert approved_count >= 1
            assert rejected_count >= 1

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_safety_validation(self):
        """Test AI safety mechanisms."""
        wish = HeadlessWish(auto_approve=False)
        wish = setup_mocks(wish)

        dangerous_plans = []

        @wish.on_event(EventType.PLAN_APPROVAL_REQUIRED)
        async def check_safety(event):
            from fixtures.mocks import get_plan_from_event
            plan = get_plan_from_event(event)

            # Check for dangerous patterns
            for step in plan.steps:
                for pattern in DANGEROUS_PATTERNS:
                    if re.search(pattern, step.command):
                        dangerous_plans.append(plan)
                        return "reject"

            return "approve"

        session = await wish.start_session()

        try:
            # Safe command
            result = await session.send_prompt("scan for vulnerabilities")
            assert result.result is not None

            # The mock should not generate dangerous commands,
            # but if it did, they would be caught
            assert len(dangerous_plans) == 0

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_adaptive_suggestions(self):
        """Test AI provides adaptive suggestions based on findings."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        session = await wish.start_session()

        try:
            # Create context with vulnerable service
            await session.send_prompt("scan 10.10.10.3")
            await session.send_prompt("found Samba 3.0.20 on port 445")

            # Ask for suggestions
            result = await session.send_prompt("what vulnerabilities should I check for?")

            # Should mention CVE-2007-2447 or username map script
            response_lower = result.result.lower()
            assert any(indicator in response_lower for indicator in
                      ["cve-2007-2447", "username map", "command injection", "exploit"])

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_plan_modification(self):
        """Test modifying plans before execution."""
        wish = HeadlessWish(auto_approve=False)
        wish = setup_mocks(wish)

        modified_plans = []

        @wish.on_event(EventType.PLAN_APPROVAL_REQUIRED)
        async def modify_and_approve(event):
            from fixtures.mocks import get_plan_from_event
            plan = get_plan_from_event(event)

            # Modify nmap commands to add -v flag
            modified = False
            for step in plan.steps:
                if step.tool_name == "nmap" and "-v" not in step.command:
                    step.command += " -v"
                    modified = True

            if modified:
                modified_plans.append(plan)

            return "approve"

        session = await wish.start_session()

        try:
            # Generate plan that will be modified
            await session.send_prompt("scan 10.10.10.3")

            # Verify modification happened
            assert len(modified_plans) > 0
            modified_plan = modified_plans[0]

            nmap_steps = [s for s in modified_plan.steps if s.tool_name == "nmap"]
            assert all("-v" in step.command for step in nmap_steps)

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_error_handling_in_planning(self):
        """Test AI handles planning errors gracefully."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        # Track errors
        errors = []

        @wish.on_event(EventType.ERROR_OCCURRED)
        async def on_error(event):
            errors.append(event.data)

        session = await wish.start_session()

        try:
            # Even with malformed input, should handle gracefully
            result = await session.send_prompt("")
            assert result.result is not None  # Should provide some response

            # Very long input
            long_input = "scan " + "10.10.10.10 " * 100
            result = await session.send_prompt(long_input)
            assert result.result is not None

            # Special characters
            result = await session.send_prompt("scan $(whoami)")
            assert result.result is not None

        finally:
            await session.end()
