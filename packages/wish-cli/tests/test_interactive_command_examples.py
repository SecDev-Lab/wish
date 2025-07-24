"""Test interactive command example display functionality."""

from unittest.mock import AsyncMock, Mock

import pytest
from wish_ai.planning.models import Plan, PlanStep, RiskLevel, StepStatus

from wish_cli.core.command_dispatcher import CommandDispatcher


@pytest.mark.asyncio
async def test_show_interactive_command_examples():
    """Test that interactive commands show examples instead of executing."""
    # Create mocks
    ui_manager = Mock()
    ui_manager.print = Mock()
    ui_manager.print_warning = Mock()
    ui_manager.print_info = Mock()

    state_manager = Mock()

    # Create dispatcher
    dispatcher = CommandDispatcher(
        ui_manager=ui_manager,
        state_manager=state_manager,
        session_manager=None,
        conversation_manager=None,
        plan_generator=None,
        tool_executor=None,
        c2_connector=None,
        retriever=None,
    )

    # Create test step
    ssh_step = PlanStep(
        tool_name="ssh",
        command="ssh user@example.com",
        purpose="Connect to remote server",
        expected_result="SSH connection established",
        risk_level=RiskLevel.LOW,
        status=StepStatus.PENDING,
    )

    # Test the method
    await dispatcher._show_interactive_command_examples("ssh user@example.com", ssh_step)

    # Verify output
    assert ui_manager.print.called

    # Check that key information was displayed
    calls = [str(call) for call in ui_manager.print.call_args_list]
    all_output = " ".join(calls)

    # Should show command info
    assert "ssh user@example.com" in all_output
    assert "SSH client" in all_output
    assert "Connect to remote server" in all_output

    # Should show usage patterns
    assert "Common Usage Patterns" in all_output
    assert "ssh user@hostname" in all_output
    assert "ssh -p 2222" in all_output

    # Should show manual execution guidance
    assert "To execute this command manually" in all_output
    assert "Open a new terminal" in all_output

    # Should show tips
    assert "Tips:" in all_output
    assert "Use -v for verbose" in all_output


@pytest.mark.asyncio
async def test_handle_interactive_plan():
    """Test handling a plan with both interactive and non-interactive steps."""
    # Create mocks
    ui_manager = Mock()
    ui_manager.print_warning = Mock()
    ui_manager.print_info = Mock()
    ui_manager.print_step_completion = Mock()
    ui_manager.start_background_job = AsyncMock()
    ui_manager.job_manager = Mock()
    ui_manager.job_manager.generate_job_id = Mock(side_effect=["job_001", "job_002"])

    tool_executor = AsyncMock()
    tool_executor.execute_command = AsyncMock(return_value=Mock(success=True, stdout="Success"))

    dispatcher = CommandDispatcher(
        ui_manager=ui_manager,
        state_manager=Mock(),
        session_manager=Mock(),
        conversation_manager=Mock(),
        plan_generator=Mock(),
        tool_executor=tool_executor,
        c2_connector=None,
        retriever=None,
    )

    # Mock the show examples method
    dispatcher._show_interactive_command_examples = AsyncMock()

    # Create plan with mixed steps
    plan = Plan(
        description="Mixed plan",
        rationale="Test",
        steps=[
            PlanStep(
                tool_name="nmap",
                command="nmap -sV target",
                purpose="Scan services",
                expected_result="Service list",
                risk_level=RiskLevel.LOW,
                status=StepStatus.PENDING,
            ),
            PlanStep(
                tool_name="ssh",
                command="ssh user@target",
                purpose="Connect via SSH",
                expected_result="SSH session",
                risk_level=RiskLevel.LOW,
                status=StepStatus.PENDING,
            ),
        ],
    )

    interactive_steps = [plan.steps[1]]  # ssh step

    # Execute
    await dispatcher._handle_interactive_plan(plan, interactive_steps)

    # Verify warnings shown
    ui_manager.print_warning.assert_called_with(
        "This plan contains interactive commands that cannot be executed automatically."
    )

    # Verify interactive step showed examples FIRST (before background jobs)
    dispatcher._show_interactive_command_examples.assert_called_once()
    call_args = dispatcher._show_interactive_command_examples.call_args
    assert "ssh user@target" in str(call_args)

    # Verify non-interactive step was started as background job
    assert ui_manager.start_background_job.called
    bg_job_call = ui_manager.start_background_job.call_args
    assert "nmap" in str(bg_job_call)


@pytest.mark.asyncio
async def test_get_usage_patterns():
    """Test that usage patterns are returned for known commands."""
    dispatcher = CommandDispatcher(
        ui_manager=Mock(),
        state_manager=Mock(),
        session_manager=None,
        conversation_manager=None,
        plan_generator=None,
        tool_executor=None,
        c2_connector=None,
        retriever=None,
    )

    # Test SSH patterns
    ssh_patterns = dispatcher._get_usage_patterns("ssh", "ssh user@host")
    assert len(ssh_patterns) > 0
    assert any("-p 2222" in p for p in ssh_patterns)
    assert any("-i keyfile" in p for p in ssh_patterns)

    # Test MySQL patterns
    mysql_patterns = dispatcher._get_usage_patterns("mysql", "mysql -h host -u root -p")
    assert len(mysql_patterns) > 0
    assert any("-P 3306" in p for p in mysql_patterns)

    # Test unknown command
    unknown_patterns = dispatcher._get_usage_patterns("unknown", "unknown command")
    assert len(unknown_patterns) == 0


@pytest.mark.asyncio
async def test_get_command_tips():
    """Test that helpful tips are returned for commands."""
    dispatcher = CommandDispatcher(
        ui_manager=Mock(),
        state_manager=Mock(),
        session_manager=None,
        conversation_manager=None,
        plan_generator=None,
        tool_executor=None,
        c2_connector=None,
        retriever=None,
    )

    # Test SSH tips
    ssh_tips = dispatcher._get_command_tips("ssh")
    assert len(ssh_tips) > 0
    assert any("verbose" in tip for tip in ssh_tips)

    # Test MySQL tips
    mysql_tips = dispatcher._get_command_tips("mysql")
    assert len(mysql_tips) > 0
    assert any("default credentials" in tip for tip in mysql_tips)

    # Test unknown command
    unknown_tips = dispatcher._get_command_tips("unknown")
    assert len(unknown_tips) == 0


@pytest.mark.asyncio
async def test_interactive_hints_shown_immediately():
    """Test that interactive hints are shown immediately, not after non-interactive completion."""
    # Create mocks
    ui_manager = Mock()
    ui_manager.print_warning = Mock()
    ui_manager.print_info = Mock()
    ui_manager.start_background_job = AsyncMock()
    ui_manager.job_manager = Mock()
    ui_manager.job_manager.generate_job_id = Mock(return_value="job_001")

    dispatcher = CommandDispatcher(
        ui_manager=ui_manager,
        state_manager=Mock(),
        session_manager=Mock(),
        conversation_manager=Mock(),
        plan_generator=Mock(),
        tool_executor=Mock(),
        c2_connector=None,
        retriever=None,
    )

    # Mock the show examples method to track call order
    call_order = []

    async def mock_show_examples(command, step):
        call_order.append("interactive_examples")

    async def mock_start_background_job(**kwargs):
        call_order.append("background_job")

    dispatcher._show_interactive_command_examples = mock_show_examples
    ui_manager.start_background_job = mock_start_background_job

    # Create plan with both types of steps
    plan = Plan(
        description="Mixed plan",
        rationale="Test order",
        steps=[
            PlanStep(
                tool_name="nmap",
                command="nmap -sV target",
                purpose="Scan services",
                expected_result="Service list",
                risk_level=RiskLevel.LOW,
                status=StepStatus.PENDING,
            ),
            PlanStep(
                tool_name="ssh",
                command="ssh user@target",
                purpose="Connect via SSH",
                expected_result="SSH session",
                risk_level=RiskLevel.LOW,
                status=StepStatus.PENDING,
            ),
        ],
    )

    interactive_steps = [plan.steps[1]]  # ssh step

    # Execute
    await dispatcher._handle_interactive_plan(plan, interactive_steps)

    # Verify that interactive examples are shown BEFORE background jobs are started
    assert call_order == ["interactive_examples", "background_job"]


@pytest.mark.asyncio
async def test_advanced_interactive_detection():
    """Test the advanced interactive command detection logic."""
    from wish_cli.core.command_dispatcher import is_interactive_command

    # Test rpcclient (should be interactive)
    assert is_interactive_command("rpcclient -U '' 10.10.10.3") is True
    assert is_interactive_command("rpcclient") is True

    # Test smbclient variations
    assert is_interactive_command("smbclient -L //10.10.10.3 -N") is False  # List shares, non-interactive
    assert is_interactive_command("smbclient //10.10.10.3/share") is True  # Connect to share, interactive
    assert is_interactive_command("smbclient //10.10.10.3/share -c 'ls'") is False  # Command mode, non-interactive

    # Test enum4linux (should be non-interactive)
    assert is_interactive_command("enum4linux -a 10.10.10.3") is False

    # Test python variations
    assert is_interactive_command("python") is True  # REPL
    assert is_interactive_command("python -c 'print(1)'") is False  # One-liner
    assert is_interactive_command("python script.py") is False  # Script execution

    # Test nmap (generally non-interactive)
    assert is_interactive_command("nmap -sV 10.10.10.3") is False
    assert is_interactive_command("nmap --script-trace 10.10.10.3") is True  # Interactive trace mode

    # Test impacket tools
    assert is_interactive_command("impacket-psexec") is True
    assert is_interactive_command("impacket-wmiexec") is True

    # Test crackmapexec (non-interactive)
    assert is_interactive_command("crackmapexec smb 10.10.10.3") is False


@pytest.mark.asyncio
async def test_background_execution_safety_check():
    """Test that interactive commands are blocked during background execution."""
    from unittest.mock import AsyncMock, Mock

    from wish_ai.planning.models import PlanStep, RiskLevel, StepStatus

    # Create mocks
    ui_manager = Mock()
    ui_manager.print_error = Mock()
    ui_manager.print_info = Mock()
    tool_executor = AsyncMock()

    dispatcher = CommandDispatcher(
        ui_manager=ui_manager,
        state_manager=Mock(),
        session_manager=Mock(),
        conversation_manager=Mock(),
        plan_generator=Mock(),
        tool_executor=tool_executor,
        c2_connector=None,
        retriever=None,
    )

    # Mock _expand_command_variables to return the command as-is
    dispatcher._expand_command_variables = AsyncMock(side_effect=lambda x: x)

    # Create a step with an interactive command
    interactive_step = PlanStep(
        tool_name="rpcclient",
        command="rpcclient -U '' 10.10.10.3",
        purpose="RPC enumeration",
        expected_result="RPC information",
        risk_level=RiskLevel.LOW,
        status=StepStatus.PENDING,
    )

    # Execute the step
    result = await dispatcher._execute_step(interactive_step, "test_job")

    # Verify that execution was blocked
    assert result["success"] is False
    assert "Interactive command" in result["error"]
    assert "cannot run in background" in result["error"]

    # Verify that error messages were shown
    ui_manager.print_error.assert_called()
    ui_manager.print_info.assert_called()

    # Verify that tool_executor was NOT called
    tool_executor.execute_command.assert_not_called()
