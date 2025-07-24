"""
Tests for context building module.
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock

import pytest
from wish_models import EngagementState, Finding, Host, Service, Target

from wish_ai.context import ContextBuilder, PromptTemplates


class TestPromptTemplates:
    """Tests for PromptTemplates class."""

    def test_init(self):
        """Test PromptTemplates initialization."""
        templates = PromptTemplates()
        assert isinstance(templates, PromptTemplates)

    def test_system_prompt_base(self):
        """Test base system prompt."""
        templates = PromptTemplates()
        prompt = templates.system_prompt_base

        assert "WISH" in prompt
        assert "penetration testing" in prompt
        assert "Response Structure" in prompt

    def test_mode_specific_prompts(self):
        """Test mode-specific prompt additions."""
        templates = PromptTemplates()

        recon_prompt = templates.get_mode_specific_prompt("recon")
        assert "Reconnaissance" in recon_prompt
        assert "network discovery" in recon_prompt.lower()

        enum_prompt = templates.get_mode_specific_prompt("enum")
        assert "Enumeration" in enum_prompt
        assert "gobuster" in enum_prompt

        exploit_prompt = templates.get_mode_specific_prompt("exploit")
        assert "Exploitation" in exploit_prompt
        assert "confirmation before running exploits" in exploit_prompt

    def test_build_context_prompt(self):
        """Test complete prompt building."""
        templates = PromptTemplates()

        context = {"mode": "recon", "state": {"active_hosts_count": 5, "open_services_count": 20, "findings_count": 3}}

        prompt = templates.build_context_prompt("Scan the network", context)

        assert "WISH" in prompt
        assert "Reconnaissance" in prompt
        assert "Active Hosts**: 5" in prompt
        assert "Scan the network" in prompt

    def test_error_response_templates(self):
        """Test error response templates."""
        templates = PromptTemplates()

        out_of_scope = templates.get_error_response_template("out_of_scope")
        assert "Out of Scope" in out_of_scope

        insufficient_info = templates.get_error_response_template("insufficient_info")
        assert "Need More Information" in insufficient_info

    def test_rich_console_format(self):
        """Test Rich Console formatting specifications."""
        templates = PromptTemplates()
        format_specs = templates.get_rich_console_format()

        assert "command" in format_specs
        assert "success" in format_specs
        assert "error" in format_specs
        assert format_specs["command"] == "cyan"
        assert format_specs["success"] == "green"


class TestContextBuilder:
    """Tests for ContextBuilder class."""

    @pytest.fixture
    def mock_retriever(self):
        """Mock retriever for testing."""
        retriever = Mock()
        retriever.search = AsyncMock()
        return retriever

    @pytest.fixture
    def sample_engagement_state(self):
        """Sample engagement state for testing."""
        from wish_models import SessionMetadata

        session_metadata = SessionMetadata(session_id="test-session", created_at=datetime.now())

        state = EngagementState(name="Test Engagement", session_metadata=session_metadata)

        # Add targets
        target = Target(scope="192.168.1.0/24", scope_type="cidr", in_scope=True)
        state.add_target(target)

        # Add hosts with services
        host1 = Host(ip_address="192.168.1.100", discovered_by="test", status="up")
        host1.add_service(
            Service(port=80, protocol="tcp", state="open", service_name="http", host_id=host1.id, discovered_by="test")
        )
        host1.add_service(
            Service(port=22, protocol="tcp", state="open", service_name="ssh", host_id=host1.id, discovered_by="test")
        )
        state.hosts[host1.id] = host1

        host2 = Host(ip_address="192.168.1.101", discovered_by="test", status="up")
        host2.add_service(
            Service(
                port=443, protocol="tcp", state="open", service_name="https", host_id=host2.id, discovered_by="test"
            )
        )
        state.hosts[host2.id] = host2

        # Add findings
        finding = Finding(
            title="Open SSH service",
            description="SSH service detected",
            category="information_disclosure",
            severity="medium",
            target_type="service",
            host_id=host1.id,
            discovered_by="test",
        )
        state.findings[finding.id] = finding

        return state

    def test_init(self, mock_retriever):
        """Test ContextBuilder initialization."""
        builder = ContextBuilder(retriever=mock_retriever, max_tokens=4000)
        assert builder.retriever == mock_retriever
        assert builder.max_tokens == 4000
        assert isinstance(builder.templates, PromptTemplates)

    def test_init_without_retriever(self):
        """Test ContextBuilder initialization without retriever."""
        builder = ContextBuilder()
        assert builder.retriever is None
        assert builder.max_tokens == 8000

    @pytest.mark.asyncio
    async def test_build_context_basic(self, sample_engagement_state):
        """Test basic context building without retriever."""
        builder = ContextBuilder()

        context = await builder.build_context(user_input="Scan the network", engagement_state=sample_engagement_state)

        assert context["user_input"] == "Scan the network"
        assert context["mode"] == "recon"
        assert "timestamp" in context
        assert "state" in context

        # Check state summary
        state = context["state"]
        assert state["active_hosts_count"] == 2
        assert state["open_services_count"] == 3
        assert state["findings_count"] == 1

    @pytest.mark.asyncio
    async def test_build_context_with_knowledge(self, mock_retriever, sample_engagement_state):
        """Test context building with knowledge retrieval."""
        # Mock retriever response
        mock_retriever.search.return_value = [
            {
                "title": "SSH Enumeration",
                "content": "SSH service enumeration techniques...",
                "score": 0.9,
                "source": "HackTricks",
            }
        ]

        builder = ContextBuilder(retriever=mock_retriever)

        context = await builder.build_context(
            user_input="Enumerate SSH service", engagement_state=sample_engagement_state
        )

        assert "knowledge" in context
        knowledge = context["knowledge"]
        assert knowledge["total_results"] == 1
        assert len(knowledge["articles"]) == 1
        assert knowledge["articles"][0]["title"] == "SSH Enumeration"

        mock_retriever.search.assert_called_once()

    @pytest.mark.asyncio
    async def test_build_context_with_conversation(self, sample_engagement_state):
        """Test context building with conversation history."""
        builder = ContextBuilder()

        conversation_history = [
            {"role": "user", "content": "Start network scan", "timestamp": datetime.now().isoformat()},
            {
                "role": "assistant",
                "content": "I'll scan the network with nmap",
                "timestamp": datetime.now().isoformat(),
            },
        ]

        context = await builder.build_context(
            user_input="Continue enumeration",
            engagement_state=sample_engagement_state,
            conversation_history=conversation_history,
        )

        assert "conversation" in context
        conv = context["conversation"]
        assert len(conv["messages"]) == 2
        assert conv["total_messages"] == 2

    def test_generate_rag_query(self, sample_engagement_state):
        """Test RAG query generation."""
        builder = ContextBuilder()

        query = builder._generate_rag_query("Enumerate web services", sample_engagement_state)

        # Should include user input and mode keywords
        assert "Enumerate web services" in query
        assert "reconnaissance" in query

        # Should include service-specific keywords
        assert "http" in query or "web application" in query

    def test_build_state_summary(self, sample_engagement_state):
        """Test state summary building."""
        builder = ContextBuilder()

        summary = builder._build_state_summary(sample_engagement_state)

        assert summary["mode"] == "recon"
        assert summary["active_hosts_count"] == 2
        assert summary["open_services_count"] == 3
        assert summary["findings_count"] == 1
        assert summary["severity_counts"]["medium"] == 1
        assert "http:80" in summary["common_services"]

    def test_determine_phase(self, sample_engagement_state):
        """Test phase determination."""
        builder = ContextBuilder()

        # With hosts but no findings -> enumeration
        sample_engagement_state.findings.clear()
        phase = builder._determine_phase(sample_engagement_state)
        assert phase == "enumeration"

        # With findings -> vulnerability_assessment or exploitation
        finding = Finding(
            title="Test finding",
            description="Test",
            category="vulnerability",
            severity="medium",
            target_type="host",
            host_id=list(sample_engagement_state.hosts.values())[0].id,
            discovered_by="test",
        )
        sample_engagement_state.findings[finding.id] = finding
        phase = builder._determine_phase(sample_engagement_state)
        assert phase == "vulnerability_assessment"

        # With high severity findings -> exploitation
        high_finding = Finding(
            title="Critical vuln",
            description="Critical vulnerability",
            category="vulnerability",
            severity="high",
            target_type="host",
            host_id=list(sample_engagement_state.hosts.values())[0].id,
            discovered_by="test",
        )
        sample_engagement_state.findings[high_finding.id] = high_finding
        phase = builder._determine_phase(sample_engagement_state)
        assert phase == "exploitation"

    def test_prioritize_conversation_history(self):
        """Test conversation history prioritization."""
        builder = ContextBuilder()

        now = datetime.now()
        old_time = now - timedelta(hours=3)

        history = [
            {"content": "Old message", "timestamp": old_time.isoformat()},
            {"content": "Recent command execution: nmap scan", "timestamp": now.isoformat()},
            {"content": "Error occurred during scan", "timestamp": (now - timedelta(minutes=30)).isoformat()},
        ]

        prioritized = builder._prioritize_conversation_history(history)

        # Recent command execution should be first (high importance + recent)
        assert "command execution" in prioritized[0]["content"]

        # Error message should be second (high importance but less recent)
        assert "Error occurred" in prioritized[1]["content"]

        # Old message should be last
        assert "Old message" in prioritized[2]["content"]

    def test_extract_actions_from_history(self):
        """Test action extraction from history."""
        builder = ContextBuilder()

        messages = [
            {"content": "Running nmap scan on target"},
            {"content": "Starting gobuster directory enumeration"},
            {"content": "Launching nikto web scan"},
            {"content": "Using hydra for credential attacks"},
            {"content": "Just a regular conversation message"},
        ]

        actions = builder._extract_actions_from_history(messages)

        expected_actions = [
            "network scanning",
            "directory enumeration",
            "credential attacks",
        ]

        for action in expected_actions:
            assert action in actions

        # Should not include non-action messages
        assert len(actions) == 3
