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
        context={"current_directory": "/home/user"}
    )

    # Create the graph
    graph = create_command_generation_graph(settings_obj=settings)

    # Act
    result = graph.invoke(initial_state)

    # Assert
    assert result is not None
    assert hasattr(result, "generated_command") or "generated_command" in result

    # Get the generated command
    generated_command = (
        result.generated_command if hasattr(result, "generated_command") else result["generated_command"]
    )

    # Verify the command is related to listing files
    assert "ls" in generated_command.command
    assert "file" in generated_command.explanation.lower() or "list" in generated_command.explanation.lower()


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
            created_at=UtcDatetime.now()
        )
    ]

    # Create the initial state with feedback
    initial_state = GraphState(
        query="List files in SMB share",
        context={"current_directory": "/home/user"},
        act_result=act_result
    )

    # Create the graph
    graph = create_command_generation_graph(settings_obj=settings)

    # Act
    result = graph.invoke(initial_state)

    # Assert
    assert result is not None
    assert hasattr(result, "generated_command") or "generated_command" in result

    # Get the generated command
    generated_command = (
        result.generated_command if hasattr(result, "generated_command") else result["generated_command"]
    )

    # Verify the command is related to SMB and contains network error handling
    assert "smbclient" in generated_command.command
    assert any(term in generated_command.explanation.lower() for term in ["network", "connection", "error"])


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
            created_at=UtcDatetime.now()
        )
    ]

    # Create the initial state with feedback
    initial_state = GraphState(
        query="Conduct a full port scan on IP 10.10.10.40",
        context={"current_directory": "/home/user"},
        act_result=act_result
    )

    # Create the graph
    graph = create_command_generation_graph(settings_obj=settings)

    # Act
    result = graph.invoke(initial_state)

    # Assert
    assert result is not None
    assert hasattr(result, "generated_command") or "generated_command" in result

    # Get the generated command
    generated_command = (
        result.generated_command if hasattr(result, "generated_command") else result["generated_command"]
    )

    # Verify the command is related to port scanning and addresses the timeout
    assert any(term in generated_command.command for term in ["scan", "10.10.10.40"])
    assert any(term in generated_command.explanation.lower() for term in ["fast", "timeout", "alternative"])


def test_command_generation_with_interactive_command(settings):
    """Test command generation with an interactive command request."""
    # Create the initial state
    initial_state = GraphState(
        query="Start an interactive Python shell",
        context={"current_directory": "/home/user"}
    )

    # Create the graph
    graph = create_command_generation_graph(settings_obj=settings)

    # Act
    result = graph.invoke(initial_state)

    # Assert
    assert result is not None
    assert hasattr(result, "generated_command") or "generated_command" in result

    # Get the generated command
    generated_command = (
        result.generated_command if hasattr(result, "generated_command") else result["generated_command"]
    )

    # Verify the command is related to Python and is non-interactive
    assert "python" in generated_command.command.lower()
    assert any(term in generated_command.explanation.lower() for term in ["python", "shell", "interactive"])
