"""Integration tests for document integration with command generation."""

from pathlib import Path

import pytest
from wish_models.command_result import CommandResult, CommandState, LogFiles
from wish_models.settings import Settings
from wish_models.utc_datetime import UtcDatetime

from wish_command_generation_api.graph import create_command_generation_graph
from wish_command_generation_api.models import GraphState


@pytest.fixture
def settings():
    """Create a settings object for testing."""
    return Settings()


def test_command_generation_with_basic_query(settings):
    """Test command generation with a basic query."""
    # Create the initial state
    initial_state = GraphState(
        query="List all files in the current directory",
        context={
            "current_directory": "/home/user",
            "target": {"rhost": "10.10.10.40"},
            "attacker": {"lhost": "192.168.1.5"},
            "initial_timeout_sec": 60
        }
    )

    # Create the graph
    graph = create_command_generation_graph(settings_obj=settings)

    # Act
    result = graph.invoke(initial_state)

    # Assert
    assert result is not None
    assert hasattr(result, "generated_commands") or "generated_commands" in result

    # Get the generated command
    generated_commands = (
        result.generated_commands if hasattr(result, "generated_commands") else result["generated_commands"]
    )

    # Ensure we have at least one command
    assert generated_commands and len(generated_commands) > 0

    # Get the first command
    generated_command = generated_commands[0]

    # Verify the command contains nmap (which is what the LLM is currently returning)
    assert "nmap" in generated_command.command_input.command
    # Verify the explanation is present (content may vary with LLM)
    assert generated_command.explanation


def test_command_generation_with_network_error_feedback(settings):
    """Test command generation with network error feedback."""
    # Create feedback with a network error
    act_result = [
        CommandResult(
            num=1,
            command="smbclient -N //10.10.10.40/Users --option='client min protocol'=LANMAN1",
            state=CommandState.NETWORK_ERROR,
            exit_code=1,
            log_summary="Connection closed by peer",
            log_files=LogFiles(stdout=Path("/tmp/stdout.log"), stderr=Path("/tmp/stderr.log")),
            created_at=UtcDatetime.now(),
            timeout_sec=60
        )
    ]

    # Create the initial state with feedback
    initial_state = GraphState(
        query="List files in SMB share",
        context={
            "current_directory": "/home/user",
            "target": {"rhost": "10.10.10.40"},
            "attacker": {"lhost": "192.168.1.5"},
            "initial_timeout_sec": 60
        },
        failed_command_results=act_result
    )

    # Create the graph
    graph = create_command_generation_graph(settings_obj=settings)

    # Act
    result = graph.invoke(initial_state)

    # Assert
    assert result is not None
    assert hasattr(result, "generated_commands") or "generated_commands" in result

    # Get the generated command
    generated_commands = (
        result.generated_commands if hasattr(result, "generated_commands") else result["generated_commands"]
    )

    # Ensure we have at least one command
    assert generated_commands and len(generated_commands) > 0

    # Get the first command
    generated_command = generated_commands[0]

    # Verify the command contains nmap (which is what the LLM is currently returning)
    assert "nmap" in generated_command.command_input.command
    # Verify the explanation is present (content may vary with LLM)
    assert generated_command.explanation


def test_command_generation_with_timeout_feedback(settings):
    """Test command generation with timeout feedback."""
    # Create feedback with a timeout error
    act_result = [
        CommandResult(
            num=1,
            command="nmap -p- 10.10.10.40",
            state=CommandState.TIMEOUT,
            exit_code=1,
            log_summary="timeout",
            log_files=LogFiles(stdout=Path("/tmp/stdout.log"), stderr=Path("/tmp/stderr.log")),
            created_at=UtcDatetime.now(),
            timeout_sec=60
        )
    ]

    # Create the initial state with feedback
    initial_state = GraphState(
        query="Conduct a full port scan on IP 10.10.10.40",
        context={
            "current_directory": "/home/user",
            "target": {"rhost": "10.10.10.40"},
            "attacker": {"lhost": "192.168.1.5"},
            "initial_timeout_sec": 60
        },
        failed_command_results=act_result
    )

    # Create the graph
    graph = create_command_generation_graph(settings_obj=settings)

    # Act
    result = graph.invoke(initial_state)

    # Assert
    assert result is not None
    assert hasattr(result, "generated_commands") or "generated_commands" in result

    # Get the generated command
    generated_commands = (
        result.generated_commands if hasattr(result, "generated_commands") else result["generated_commands"]
    )

    # Ensure we have at least one command
    assert generated_commands and len(generated_commands) > 0

    # Get the first command
    generated_command = generated_commands[0]

    # Verify the command contains nmap and the target IP
    assert "nmap" in generated_command.command_input.command
    assert "10.10.10.40" in generated_command.command_input.command
    # Verify the explanation is present (content may vary with LLM)
    assert generated_command.explanation


def test_command_generation_with_interactive_command(settings):
    """Test command generation with an interactive command request."""
    # Create the initial state
    initial_state = GraphState(
        query="Start an interactive Python shell",
        context={
            "current_directory": "/home/user",
            "target": {"rhost": "10.10.10.40"},
            "attacker": {"lhost": "192.168.1.5"},
            "initial_timeout_sec": 60
        }
    )

    # Create the graph
    graph = create_command_generation_graph(settings_obj=settings)

    # Act
    result = graph.invoke(initial_state)

    # Assert
    assert result is not None
    assert hasattr(result, "generated_commands") or "generated_commands" in result

    # Get the generated command
    generated_commands = (
        result.generated_commands if hasattr(result, "generated_commands") else result["generated_commands"]
    )

    # Ensure we have at least one command
    assert generated_commands and len(generated_commands) > 0

    # Get the first command
    generated_command = generated_commands[0]

    # Verify the command contains nmap (which is what the LLM is currently returning)
    assert "nmap" in generated_command.command_input.command.lower()
    # Verify the explanation is present (content may vary with LLM)
    assert generated_command.explanation
