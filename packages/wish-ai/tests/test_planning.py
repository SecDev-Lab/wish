"""
Tests for planning module.
"""

from unittest.mock import AsyncMock, Mock

import pytest
from wish_models import EngagementState, Host, Service, Target

from wish_ai.planning import Plan, PlanGenerator, PlanStep, RiskLevel, StepStatus
from wish_ai.planning.generator import PlanGenerationError


class TestPlanStep:
    """Tests for PlanStep data class."""

    def test_plan_step_creation(self):
        """Test basic PlanStep creation."""
        step = PlanStep(
            tool_name="nmap",
            command="nmap -sV target.com",
            purpose="Service detection",
            expected_result="Open ports and services",
        )

        assert step.tool_name == "nmap"
        assert step.command == "nmap -sV target.com"
        assert step.purpose == "Service detection"
        assert step.expected_result == "Open ports and services"
        assert step.risk_level == RiskLevel.LOW
        assert step.status == StepStatus.PENDING

    def test_plan_step_validation(self):
        """Test PlanStep validation."""
        # Empty tool name should raise error
        with pytest.raises(ValueError, match="tool_name cannot be empty"):
            PlanStep(tool_name="", command="test", purpose="test", expected_result="test")

        # Empty command should raise error
        with pytest.raises(ValueError, match="command cannot be empty"):
            PlanStep(tool_name="test", command="", purpose="test", expected_result="test")

    def test_high_risk_auto_confirmation(self):
        """Test that high-risk tools automatically require confirmation."""
        step = PlanStep(
            tool_name="metasploit",
            command="use exploit/windows/smb/ms17_010_eternalblue",
            purpose="Exploit SMB vulnerability",
            expected_result="Shell access",
            risk_level=RiskLevel.HIGH,
        )

        assert step.requires_confirmation is True

    def test_is_ready_to_execute(self):
        """Test prerequisite checking."""
        step = PlanStep(
            tool_name="nmap",
            command="nmap -A target",
            purpose="Detailed scan",
            expected_result="Detailed info",
            prerequisites=["step_0", "step_1"],
        )

        # Should not be ready when prerequisites not met
        assert step.is_ready_to_execute([]) is False
        assert step.is_ready_to_execute(["step_0"]) is False

        # Should be ready when all prerequisites met
        assert step.is_ready_to_execute(["step_0", "step_1"]) is True
        assert step.is_ready_to_execute(["step_0", "step_1", "step_2"]) is True

    def test_to_dict(self):
        """Test dictionary conversion."""
        step = PlanStep(
            tool_name="nmap", command="nmap -sV target", purpose="Test purpose", expected_result="Test result"
        )

        result = step.to_dict()
        assert result["tool_name"] == "nmap"
        assert result["command"] == "nmap -sV target"
        assert result["risk_level"] == "low"
        assert result["requires_confirmation"] == "False"


class TestPlan:
    """Tests for Plan data class."""

    def test_plan_creation(self):
        """Test basic Plan creation."""
        steps = [
            PlanStep("nmap", "nmap -sV target", "Scan", "Open ports"),
            PlanStep("gobuster", "gobuster dir -u http://target", "Dir enum", "Hidden dirs"),
        ]

        plan = Plan(description="Test plan", steps=steps, rationale="For testing", estimated_duration=30)

        assert plan.description == "Test plan"
        assert len(plan.steps) == 2
        assert plan.rationale == "For testing"
        assert plan.estimated_duration == 30
        assert plan.total_steps == 2
        assert plan.mode == "recon"  # default

    def test_plan_validation(self):
        """Test Plan validation."""
        # Empty description should raise error
        with pytest.raises(ValueError, match="description cannot be empty"):
            Plan(description="", steps=[], rationale="test")

        # No steps is now allowed for knowledge-based responses
        plan = Plan(description="test", steps=[], rationale="test")
        assert plan.total_steps == 0
        assert plan.completion_percentage == 0.0  # Empty plan returns 0% completion

        # Empty rationale should raise error
        with pytest.raises(ValueError, match="rationale cannot be empty"):
            Plan(description="test", steps=[Mock()], rationale="")

    def test_high_risk_steps(self):
        """Test high risk step identification."""
        steps = [
            PlanStep("nmap", "nmap target", "Scan", "Results", risk_level=RiskLevel.LOW),
            PlanStep("metasploit", "exploit", "Exploit", "Shell", risk_level=RiskLevel.HIGH),
            PlanStep("sqlmap", "sqlmap -u url", "SQL injection", "Data", risk_level=RiskLevel.CRITICAL),
        ]

        plan = Plan("Test", steps, "Testing")
        high_risk = plan.high_risk_steps

        assert len(high_risk) == 2
        assert high_risk[0].tool_name == "metasploit"
        assert high_risk[1].tool_name == "sqlmap"

    def test_completion_percentage(self):
        """Test completion percentage calculation."""
        steps = [
            PlanStep("tool1", "cmd1", "purpose1", "result1"),
            PlanStep("tool2", "cmd2", "purpose2", "result2"),
            PlanStep("tool3", "cmd3", "purpose3", "result3"),
        ]

        plan = Plan("Test", steps, "Testing")

        # Initially 0%
        assert plan.completion_percentage == 0.0

        # Mark first step complete
        plan.mark_step_completed(0)
        assert plan.completion_percentage == pytest.approx(33.33, rel=1e-2)

        # Mark second step complete
        plan.mark_step_completed(1)
        assert plan.completion_percentage == pytest.approx(66.67, rel=1e-2)

        # Mark all complete
        plan.mark_step_completed(2)
        assert plan.completion_percentage == 100.0

    def test_get_next_step(self):
        """Test getting the next executable step."""
        steps = [
            PlanStep("tool1", "cmd1", "purpose1", "result1"),  # No prerequisites
            PlanStep("tool2", "cmd2", "purpose2", "result2", prerequisites=["step_0"]),
            PlanStep("tool3", "cmd3", "purpose3", "result3", prerequisites=["step_0", "step_1"]),
        ]

        plan = Plan("Test", steps, "Testing")

        # First step should be next
        next_step = plan.get_next_step()
        assert next_step == steps[0]

        # After completing first step, second should be next
        plan.mark_step_completed(0)
        next_step = plan.get_next_step()
        assert next_step == steps[1]

        # After completing second step, third should be next
        plan.mark_step_completed(1)
        next_step = plan.get_next_step()
        assert next_step == steps[2]

        # After completing all, no next step
        plan.mark_step_completed(2)
        next_step = plan.get_next_step()
        assert next_step is None


class TestPlanGenerator:
    """Tests for PlanGenerator."""

    @pytest.fixture
    def mock_gateway(self):
        """Mock LLM gateway for testing."""
        gateway = Mock()
        gateway.generate_plan = AsyncMock()
        return gateway

    @pytest.fixture
    def sample_engagement_state(self):
        """Sample engagement state for testing."""
        from datetime import datetime

        from wish_models import SessionMetadata

        session_metadata = SessionMetadata(session_id="test-session", created_at=datetime.now())

        state = EngagementState(name="Test Engagement", session_metadata=session_metadata)

        # Add a target
        target = Target(scope="192.168.1.0/24", scope_type="cidr", in_scope=True)
        state.add_target(target)

        # Add a host with services
        host = Host(ip_address="192.168.1.100", discovered_by="test", status="up")
        host.add_service(
            Service(port=80, protocol="tcp", state="open", service_name="http", host_id=host.id, discovered_by="test")
        )
        host.add_service(
            Service(port=22, protocol="tcp", state="open", service_name="ssh", host_id=host.id, discovered_by="test")
        )
        state.hosts[host.id] = host

        return state

    def test_plan_generator_init(self, mock_gateway):
        """Test PlanGenerator initialization."""
        generator = PlanGenerator(mock_gateway)
        assert generator.llm_gateway == mock_gateway

    @pytest.mark.asyncio
    async def test_generate_plan_success(self, mock_gateway, sample_engagement_state):
        """Test successful plan generation."""
        # Mock LLM response
        mock_response = """```json
        {
            "description": "Network reconnaissance plan",
            "rationale": "Start with basic network discovery",
            "estimated_duration": 30,
            "steps": [
                {
                    "tool_name": "nmap",
                    "command": "nmap -sV 192.168.1.0/24",
                    "purpose": "Service detection",
                    "expected_result": "Open ports and services",
                    "risk_level": "low"
                }
            ]
        }
        ```"""

        mock_gateway.generate_plan.return_value = mock_response

        generator = PlanGenerator(mock_gateway)
        plan = await generator.generate_plan(user_input="Scan the network", engagement_state=sample_engagement_state)

        assert isinstance(plan, Plan)
        assert plan.description == "Network reconnaissance plan"
        assert len(plan.steps) == 1
        assert plan.steps[0].tool_name == "nmap"
        assert plan.steps[0].command == "nmap -sV 192.168.1.0/24"

    @pytest.mark.asyncio
    async def test_generate_plan_invalid_json(self, mock_gateway, sample_engagement_state):
        """Test handling of invalid JSON response."""
        mock_gateway.generate_plan.return_value = "Invalid JSON response"

        generator = PlanGenerator(mock_gateway)

        with pytest.raises(PlanGenerationError, match="No valid JSON found"):
            await generator.generate_plan(user_input="Test input", engagement_state=sample_engagement_state)

    @pytest.mark.asyncio
    async def test_generate_plan_missing_fields(self, mock_gateway, sample_engagement_state):
        """Test handling of missing required fields."""
        mock_response = """```json
        {
            "description": "Test plan"
        }
        ```"""

        mock_gateway.generate_plan.return_value = mock_response

        generator = PlanGenerator(mock_gateway)

        with pytest.raises(PlanGenerationError, match="Missing required field"):
            await generator.generate_plan(user_input="Test input", engagement_state=sample_engagement_state)

    @pytest.mark.asyncio
    async def test_generate_plan_gateway_error(self, mock_gateway, sample_engagement_state):
        """Test handling of gateway errors."""
        mock_gateway.generate_plan.side_effect = Exception("Gateway error")

        generator = PlanGenerator(mock_gateway)

        with pytest.raises(PlanGenerationError, match="Failed to generate plan"):
            await generator.generate_plan(user_input="Test input", engagement_state=sample_engagement_state)

    def test_format_targets_context(self, mock_gateway):
        """Test target context formatting."""
        generator = PlanGenerator(mock_gateway)

        # Test with targets
        targets = [
            Target(scope="192.168.1.0/24", scope_type="cidr", in_scope=True),
            Target(scope="example.com", scope_type="domain", in_scope=True),
            Target(scope="out-of-scope.com", scope_type="domain", in_scope=False),
        ]

        context = generator._format_targets_context(targets)
        assert "192.168.1.0/24" in context
        assert "example.com" in context
        assert "out-of-scope.com" not in context  # Out of scope should be excluded

    def test_format_hosts_context(self, mock_gateway):
        """Test hosts context formatting."""
        generator = PlanGenerator(mock_gateway)

        # Create test hosts
        hosts = []
        for i in range(3):
            host = Host(ip_address=f"192.168.1.{100 + i}", discovered_by="test", status="up")
            host.add_service(Service(port=80, protocol="tcp", state="open", host_id=host.id, discovered_by="test"))
            host.add_service(Service(port=22, protocol="tcp", state="open", host_id=host.id, discovered_by="test"))
            hosts.append(host)

        context = generator._format_hosts_context(hosts)
        assert "192.168.1.100" in context
        assert "2 open ports" in context

    def test_parse_plan_step(self, mock_gateway):
        """Test parsing individual plan steps."""
        generator = PlanGenerator(mock_gateway)

        step_data = {
            "tool_name": "nmap",
            "command": "nmap -sV target",
            "purpose": "Service detection",
            "expected_result": "Open ports",
            "risk_level": "medium",
            "timeout": 300,
            "requires_confirmation": True,
        }

        step = generator._parse_plan_step(step_data)

        assert step.tool_name == "nmap"
        assert step.command == "nmap -sV target"
        assert step.risk_level == RiskLevel.MEDIUM
        assert step.timeout == 300
        assert step.requires_confirmation is True
