"""Integration tests for the command generation graph with feedback."""

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


def test_graph_with_no_feedback(settings):
    """Test graph execution with no feedback (first run)."""
    # Create the initial state
    initial_state = GraphState(
        query="List all files in the current directory",
        context={
            "current_directory": "/home/user",
            "target": {"rhost": "10.10.10.40"},
            "attacker": {"lhost": "192.168.1.5"},
            "initial_timeout_sec": 60  # Add initial timeout value
        }
    )

    # Create the graph
    graph = create_command_generation_graph(settings_obj=settings)

    # Act
    result = graph.invoke(initial_state)

    # Assert
    # Verify the result contains a generated command
    assert result is not None

    # Get the generated commands (handle different result structures)
    if hasattr(result, "generated_commands"):
        generated_commands = result.generated_commands
    elif isinstance(result, dict) and "generated_commands" in result:
        generated_commands = result["generated_commands"]
    else:
        # Try to access as AddableValuesDict
        generated_commands = result.values.get("generated_commands")

    assert generated_commands is not None
    assert len(generated_commands) > 0

    # Get the first command
    generated_command = generated_commands[0]

    assert "nmap" in generated_command.command_input.command
    assert generated_command.explanation


def test_graph_with_timeout_feedback(settings):
    """Test graph execution with timeout feedback."""
    # Create feedback with a timeout error
    log_files = LogFiles(stdout=Path("/tmp/stdout.log"), stderr=Path("/tmp/stderr.log"))
    act_result = [
            CommandResult(
                num=1,
                command="nmap -p- 10.10.10.40",
                state=CommandState.TIMEOUT,
                exit_code=1,
                log_summary="timeout",
                log_files=log_files,
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
            "initial_timeout_sec": 60  # Add initial timeout value
        },
        failed_command_results=act_result,
        is_retry=False  # Set is_retry to False for unknown errors
    )

    # Create the graph
    graph = create_command_generation_graph(settings_obj=settings)

    # Act
    result = graph.invoke(initial_state)

    # Assert
    # Verify the result contains a generated command
    assert result is not None

    # Get the generated commands (handle different result structures)
    if hasattr(result, "generated_commands"):
        generated_commands = result.generated_commands
    elif isinstance(result, dict) and "generated_commands" in result:
        generated_commands = result["generated_commands"]
    else:
        # Try to access as AddableValuesDict
        generated_commands = result.values.get("generated_commands")

    assert generated_commands is not None
    assert len(generated_commands) > 0

    # Get the first command
    generated_command = generated_commands[0]

    assert "nmap" in generated_command.command_input.command
    assert "10.10.10.40" in generated_command.command_input.command
    assert generated_command.explanation


def test_graph_with_network_error_feedback(settings):
    """Test graph execution with network error feedback."""
    # Create feedback with a network error
    log_files = LogFiles(stdout=Path("/tmp/stdout.log"), stderr=Path("/tmp/stderr.log"))
    act_result = [
        CommandResult(
            num=1,
            command="nmap -p- 10.10.10.40",
            state=CommandState.NETWORK_ERROR,
            exit_code=1,
            log_summary="Connection closed by peer",
            log_files=log_files,
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
            "initial_timeout_sec": 60  # Add initial timeout value
        },
        failed_command_results=act_result,
        is_retry=False  # Set is_retry to False for unknown errors
    )

    # Create the graph
    graph = create_command_generation_graph(settings_obj=settings)

    # Act
    result = graph.invoke(initial_state)

    # Assert
    # Verify the result contains a generated command
    assert result is not None

    # Get the generated commands (handle different result structures)
    if hasattr(result, "generated_commands"):
        generated_commands = result.generated_commands
    elif isinstance(result, dict) and "generated_commands" in result:
        generated_commands = result["generated_commands"]
    else:
        # Try to access as AddableValuesDict
        generated_commands = result.values.get("generated_commands")

    assert generated_commands is not None
    assert len(generated_commands) > 0

    # Get the first command
    generated_command = generated_commands[0]

    assert "nmap" in generated_command.command_input.command
    assert "10.10.10.40" in generated_command.command_input.command
    assert generated_command.explanation


def test_graph_with_unknown_error_feedback(settings):
    """Test graph execution with unknown error feedback."""
    # Create feedback with an unknown error
    log_files = LogFiles(stdout=Path("/tmp/stdout.log"), stderr=Path("/tmp/stderr.log"))
    act_result = [
        CommandResult(
            num=1,
            command="nmap -p- 10.10.10.40",
            state=CommandState.OTHERS,
            exit_code=1,
            log_summary="Unknown error",
            log_files=log_files,
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
            "initial_timeout_sec": 60  # Add initial timeout value
        },
        failed_command_results=act_result,
        is_retry=False  # Set is_retry to False for unknown errors
    )

    # Create the graph
    graph = create_command_generation_graph(settings_obj=settings)

    # Act
    result = graph.invoke(initial_state)

    # Assert
    # Verify the result contains a generated command
    assert result is not None

    # Get the generated commands (handle different result structures)
    if hasattr(result, "generated_commands"):
        generated_commands = result.generated_commands
    elif isinstance(result, dict) and "generated_commands" in result:
        generated_commands = result["generated_commands"]
    else:
        # Try to access as AddableValuesDict
        generated_commands = result.values.get("generated_commands")

    assert generated_commands is not None
    assert len(generated_commands) > 0

    # Get the first command
    generated_command = generated_commands[0]

    assert "nmap" in generated_command.command_input.command
    assert "10.10.10.40" in generated_command.command_input.command
    assert generated_command.explanation
