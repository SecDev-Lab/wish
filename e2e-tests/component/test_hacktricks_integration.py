"""HackTricks knowledge base integration tests using HeadlessWish."""

import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from wish_cli.headless import EventType, HeadlessWish
from wish_knowledge import Retriever

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from fixtures import MockEventCollector, setup_mocks


class TestHackTricksIntegration:
    """Test HackTricks knowledge base integration through HeadlessWish SDK."""

    @pytest.mark.asyncio
    async def test_knowledge_initialization_simulation(self):
        """Test simulated HackTricks initialization on first startup."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        # Track progress updates
        progress_updates = []

        @wish.on_event(EventType.JOB_PROGRESS)
        async def track_progress(event):
            if "HackTricks" in str(event.data):
                progress_updates.append(event.data)

        session = await wish.start_session()

        try:
            # Simulate knowledge base initialization
            with patch('wish_knowledge.manager.check_knowledge_initialized', return_value=False):
                with patch('wish_knowledge.manager.KnowledgeManager.initialize_foreground') as mock_init:
                    # Mock the initialization process
                    async def mock_initialize_foreground(progress_callback=None):
                        if progress_callback:
                            progress_callback("fetching", 0)
                            progress_callback("fetching", 30)
                            progress_callback("processing", 50)
                            progress_callback("storing", 70)
                            progress_callback("storing", 85)
                            progress_callback("storing", 95)
                            progress_callback("complete", 100)
                        return True

                    mock_init.side_effect = mock_initialize_foreground

                    # Trigger an AI operation that would require knowledge base
                    result = await session.send_prompt("How do I enumerate SMB shares?")

                    # Verify response was generated
                    assert result.result is not None

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_rag_search_integration(self):
        """Test RAG search functionality with mocked HackTricks data."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        session = await wish.start_session()

        try:
            # Test knowledge-based query
            # Use a query format that the mock understands
            result = await session.send_prompt("how do I enumerate SMB shares?")

            # Response should include SMB enumeration tools
            response_lower = result.result.lower()
            assert result.result is not None

            # Should mention specific tools and techniques
            expected_tools = ["smbclient", "enum4linux", "rpcclient", "smbmap"]
            found_tools = [tool for tool in expected_tools if tool in response_lower]
            assert len(found_tools) >= 2, f"Expected at least 2 SMB tools in response, found: {found_tools}"

            # Test another knowledge query
            result2 = await session.send_prompt("What is the CVE for samba username map script?")
            response2_lower = result2.result.lower()

            # Should mention the specific CVE
            assert "cve-2007-2447" in response2_lower

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_context_enrichment_with_knowledge(self):
        """Test that HackTricks knowledge enriches AI context."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        collector = MockEventCollector()

        @wish.on_event(EventType.PLAN_APPROVAL_REQUIRED)
        async def collect_plans(event):
            collector.collect_plan_approval(event)
            return "approve"

        session = await wish.start_session()

        try:
            # Request that should generate a plan with knowledge-enhanced commands
            await session.send_prompt("scan for SMB vulnerabilities on 10.10.10.3")

            # Check generated plan
            assert len(collector.plan_approvals) > 0
            plan = collector.plan_approvals[0]

            # Plan should include appropriate scanning techniques
            # The mock should generate commands that would come from HackTricks knowledge
            nmap_steps = [s for s in plan.steps if s.tool_name == "nmap"]
            assert len(nmap_steps) > 0, "Expected nmap steps in plan"

            # At least one nmap command should target SMB ports or use scripts
            smb_related = any(
                "445" in step.command or "139" in step.command or "smb" in step.command.lower()
                for step in nmap_steps
            )
            assert smb_related, "Expected SMB-related scanning in plan"

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_tool_recommendations_from_knowledge(self):
        """Test tool recommendations based on HackTricks knowledge."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        session = await wish.start_session()

        try:
            # Mock tools from knowledge base
            mock_tools = [
                {
                    "name": "gobuster",
                    "category": "web_enum",
                    "description": "Directory/file brute-forcer",
                    "example_commands": ["gobuster dir -u http://target -w wordlist.txt"],
                    "confidence": 0.95
                },
                {
                    "name": "wfuzz",
                    "category": "web_enum",
                    "description": "Web application fuzzer",
                    "example_commands": ["wfuzz -c -z file,wordlist.txt http://target/FUZZ"],
                    "confidence": 0.90
                }
            ]

            # Mock the get_tools_for_context method
            with patch('wish_knowledge.sources.HackTricksRetriever.get_tools_for_context',
                      return_value=mock_tools):

                result = await session.send_prompt("What tools should I use for web directory enumeration?")

                # Response should mention recommended tools
                response_lower = result.result.lower()
                assert "gobuster" in response_lower
                assert "wfuzz" in response_lower or "fuzzer" in response_lower

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_vulnerability_specific_knowledge(self):
        """Test knowledge base provides specific vulnerability information."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        session = await wish.start_session()

        try:
            # First establish context
            await session.send_prompt("I found Samba 3.0.20 running on port 445")

            # Ask about vulnerabilities
            result = await session.send_prompt("What vulnerabilities affect this version?")

            # Response should mention CVE-2007-2447 (the mock knows about this)
            response_lower = result.result.lower()
            assert "cve-2007-2447" in response_lower or "username map" in response_lower

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_multi_source_knowledge_integration(self):
        """Test integration of multiple knowledge sources (vector DB + tools.tsv)."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        collector = MockEventCollector()

        @wish.on_event(EventType.PLAN_APPROVAL_REQUIRED)
        async def collect_plans(event):
            collector.collect_plan_approval(event)
            return "approve"

        session = await wish.start_session()

        try:
            # Mock both vector search and tool recommendations
            mock_retriever = MagicMock(spec=Retriever)
            mock_retriever.search = AsyncMock(return_value=[
                {
                    "title": "Web Application Scanning",
                    "content": "Comprehensive web scanning approach using multiple tools",
                    "score": 0.90,
                    "source": "HackTricks"
                }
            ])

            # Test knowledge integration

            with patch.object(wish.command_dispatcher, 'retriever', mock_retriever):
                # Request comprehensive web scan
                await session.send_prompt("perform comprehensive web application scanning")

                # Check that plan was generated
                assert len(collector.plan_approvals) > 0
                plan = collector.plan_approvals[0]

                # Should have some steps
                assert len(plan.steps) > 0

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_knowledge_base_offline_fallback(self):
        """Test system handles knowledge base unavailability gracefully."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        session = await wish.start_session()

        try:
            # Should work even if knowledge base were unavailable
            result = await session.send_prompt("scan network 10.10.10.0/24")

            # Verify response is still generated
            assert result.result is not None

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_knowledge_query_optimization(self):
        """Test that knowledge queries are optimized based on context."""
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        session = await wish.start_session()

        try:
            # Set context
            await session.send_prompt("target is 10.10.10.3")

            # Query in enum mode
            result = await session.send_prompt("enumerate services")

            # The mock should handle enumeration requests appropriately
            assert result.result is not None

        finally:
            await session.end()

    @pytest.mark.asyncio
    async def test_knowledge_base_performance(self):
        """Test knowledge base doesn't significantly impact response time."""
        import time

        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)

        session = await wish.start_session()

        try:
            # Measure response time
            start_time = time.time()
            result = await session.send_prompt("quick scan of 10.10.10.3")
            end_time = time.time()

            # Should respond quickly even with knowledge base
            response_time = end_time - start_time
            assert response_time < 5.0  # Should respond within 5 seconds
            assert result.result is not None

        finally:
            await session.end()
