"""Integration tests for the command generation graph with feedback."""

from pathlib import Path
from unittest.mock import patch

import pytest
from wish_models.command_result import CommandResult, CommandState, LogFiles
from wish_models.settings import Settings
from wish_models.utc_datetime import UtcDatetime

from wish_command_generation_api.graph import create_command_generation_graph
from wish_command_generation_api.models import GeneratedCommand, GraphState


@pytest.fixture
def settings():
    """Create a settings object for testing."""
    return Settings()


@patch("wish_command_generation_api.nodes.feedback_analyzer.analyze_feedback")
@patch("wish_command_generation_api.nodes.query_processor.process_query")
@patch("wish_command_generation_api.nodes.command_generator.generate_command")
@patch("wish_command_generation_api.nodes.command_modifier.modify_command")
@patch("wish_command_generation_api.nodes.result_formatter.format_result")
def test_graph_with_no_feedback(
    mock_format_result, mock_modify_command, mock_generate_command,
    mock_process_query, mock_analyze_feedback, settings
):
    """Test graph execution with no feedback (first run)."""
    # Arrange
    # Mock the node functions
    mock_analyze_feedback.return_value = GraphState(
        query="test query",
        context={},
        is_retry=False,
        error_type=None
    )
    mock_process_query.return_value = GraphState(
        query="test query",
        context={},
        processed_query="processed query",
        is_retry=False,
        error_type=None
    )
    mock_generate_command.return_value = GraphState(
        query="test query",
        context={},
        processed_query="processed query",
        command_candidates=["ls -la"],
        is_retry=False,
        error_type=None
    )
    mock_modify_command.return_value = GraphState(
        query="test query",
        context={},
        processed_query="processed query",
        command_candidates=["ls -la"],
        is_retry=False,
        error_type=None
    )
    mock_format_result.return_value = GraphState(
        query="test query",
        context={},
        processed_query="processed query",
        command_candidates=["ls -la"],
        generated_command=GeneratedCommand(
            command="ls -la",
            explanation="This command lists all files in the current directory, including hidden files."
        ),
        is_retry=False,
        error_type=None
    )

    # Create the initial state
    initial_state = GraphState(query="test query", context={})

    # Create the graph
    graph = create_command_generation_graph(settings_obj=settings)

    # Act
    # Use dict() to ensure we get a proper dictionary instead of AddableValuesDict
    result = dict(graph.invoke(initial_state))

    # Assert
    # Verify that the nodes were called in the correct order
    mock_analyze_feedback.assert_called_once()
    mock_process_query.assert_called_once()
    mock_generate_command.assert_called_once()
    mock_modify_command.assert_called_once()
    mock_format_result.assert_called_once()

    # Verify the result
    assert result["generated_command"].command == "ls -la"
    assert result["generated_command"].explanation == (
        "This command lists all files in the current directory, including hidden files."
    )


@patch("wish_command_generation_api.nodes.feedback_analyzer.analyze_feedback")
@patch("wish_command_generation_api.nodes.timeout_handler.handle_timeout")
@patch("wish_command_generation_api.nodes.command_generator.generate_command")
@patch("wish_command_generation_api.nodes.command_modifier.modify_command")
@patch("wish_command_generation_api.nodes.result_formatter.format_result")
def test_graph_with_timeout_feedback(
    mock_format_result, mock_modify_command, mock_generate_command,
    mock_handle_timeout, mock_analyze_feedback, settings
):
    """Test graph execution with timeout feedback."""
    # Arrange
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
            created_at=UtcDatetime.now()
        )
    ]

    # Mock the node functions
    mock_analyze_feedback.return_value = GraphState(
        query="Conduct a full port scan on IP 10.10.10.40",
        context={},
        act_result=act_result,
        is_retry=True,
        error_type="TIMEOUT"
    )
    mock_handle_timeout.return_value = GraphState(
        query="Conduct a full port scan on IP 10.10.10.40",
        context={},
        act_result=act_result,
        command_candidates=["rustscan -a 10.10.10.40"],
        is_retry=True,
        error_type="TIMEOUT"
    )
    mock_modify_command.return_value = GraphState(
        query="Conduct a full port scan on IP 10.10.10.40",
        context={},
        act_result=act_result,
        command_candidates=["rustscan -a 10.10.10.40"],
        is_retry=True,
        error_type="TIMEOUT"
    )
    mock_format_result.return_value = GraphState(
        query="Conduct a full port scan on IP 10.10.10.40",
        context={},
        act_result=act_result,
        command_candidates=["rustscan -a 10.10.10.40"],
        generated_command=GeneratedCommand(
            command="rustscan -a 10.10.10.40",
            explanation="This command performs a fast port scan using rustscan."
        ),
        is_retry=True,
        error_type="TIMEOUT"
    )

    # Create the initial state with feedback
    initial_state = GraphState(
        query="Conduct a full port scan on IP 10.10.10.40",
        context={},
        act_result=act_result
    )

    # Create the graph
    graph = create_command_generation_graph(settings_obj=settings)

    # Act
    # Use dict() to ensure we get a proper dictionary instead of AddableValuesDict
    result = dict(graph.invoke(initial_state))

    # Assert
    # Verify that the nodes were called in the correct order
    mock_analyze_feedback.assert_called_once()
    mock_handle_timeout.assert_called_once()
    mock_generate_command.assert_not_called()  # Should not be called for timeout handling
    mock_modify_command.assert_called_once()
    mock_format_result.assert_called_once()

    # Verify the result
    assert result["generated_command"].command == "rustscan -a 10.10.10.40"
    assert "fast port scan" in result["generated_command"].explanation


@patch("wish_command_generation_api.nodes.feedback_analyzer.analyze_feedback")
@patch("wish_command_generation_api.nodes.network_error_handler.handle_network_error")
@patch("wish_command_generation_api.nodes.command_generator.generate_command")
@patch("wish_command_generation_api.nodes.command_modifier.modify_command")
@patch("wish_command_generation_api.nodes.result_formatter.format_result")
def test_graph_with_network_error_feedback(
    mock_format_result, mock_modify_command, mock_generate_command,
    mock_handle_network_error, mock_analyze_feedback, settings
):
    """Test graph execution with network error feedback."""
    # Arrange
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
            created_at=UtcDatetime.now()
        )
    ]

    # Mock the node functions
    mock_analyze_feedback.return_value = GraphState(
        query="Conduct a full port scan on IP 10.10.10.40",
        context={},
        act_result=act_result,
        is_retry=True,
        error_type="NETWORK_ERROR"
    )
    mock_handle_network_error.return_value = GraphState(
        query="Conduct a full port scan on IP 10.10.10.40",
        context={},
        act_result=act_result,
        command_candidates=["nmap -Pn -p- 10.10.10.40"],
        is_retry=True,
        error_type="NETWORK_ERROR"
    )
    mock_modify_command.return_value = GraphState(
        query="Conduct a full port scan on IP 10.10.10.40",
        context={},
        act_result=act_result,
        command_candidates=["nmap -Pn -p- 10.10.10.40"],
        is_retry=True,
        error_type="NETWORK_ERROR"
    )
    mock_format_result.return_value = GraphState(
        query="Conduct a full port scan on IP 10.10.10.40",
        context={},
        act_result=act_result,
        command_candidates=["nmap -Pn -p- 10.10.10.40"],
        generated_command=GeneratedCommand(
            command="nmap -Pn -p- 10.10.10.40",
            explanation="This command performs a port scan while skipping host discovery."
        ),
        is_retry=True,
        error_type="NETWORK_ERROR"
    )

    # Create the initial state with feedback
    initial_state = GraphState(
        query="Conduct a full port scan on IP 10.10.10.40",
        context={},
        act_result=act_result
    )

    # Create the graph
    graph = create_command_generation_graph(settings_obj=settings)

    # Act
    # Use dict() to ensure we get a proper dictionary instead of AddableValuesDict
    result = dict(graph.invoke(initial_state))

    # Assert
    # Verify that the nodes were called in the correct order
    mock_analyze_feedback.assert_called_once()
    mock_handle_network_error.assert_called_once()
    mock_generate_command.assert_not_called()  # Should not be called for network error handling
    mock_modify_command.assert_called_once()
    mock_format_result.assert_called_once()

    # Verify the result
    assert result["generated_command"].command == "nmap -Pn -p- 10.10.10.40"
    assert "skipping host discovery" in result["generated_command"].explanation


@patch("wish_command_generation_api.nodes.feedback_analyzer.analyze_feedback")
@patch("wish_command_generation_api.nodes.query_processor.process_query")
@patch("wish_command_generation_api.nodes.command_generator.generate_command")
@patch("wish_command_generation_api.nodes.command_modifier.modify_command")
@patch("wish_command_generation_api.nodes.result_formatter.format_result")
def test_graph_with_unknown_error_feedback(
    mock_format_result, mock_modify_command, mock_generate_command,
    mock_process_query, mock_analyze_feedback, settings
):
    """Test graph execution with unknown error feedback."""
    # Arrange
    # Create feedback with an unknown error
    log_files = LogFiles(stdout=Path("/tmp/stdout.log"), stderr=Path("/tmp/stderr.log"))
    act_result = [
        CommandResult(
            num=1,
            command="nmap -p- 10.10.10.40",
            state=CommandState.UNKNOWN_ERROR,
            exit_code=1,
            log_summary="Unknown error",
            log_files=log_files,
            created_at=UtcDatetime.now()
        )
    ]

    # Mock the node functions
    mock_analyze_feedback.return_value = GraphState(
        query="Conduct a full port scan on IP 10.10.10.40",
        context={},
        act_result=act_result,
        is_retry=True,
        error_type=None  # Unknown error type
    )
    mock_process_query.return_value = GraphState(
        query="Conduct a full port scan on IP 10.10.10.40",
        context={},
        act_result=act_result,
        processed_query="scan all ports on 10.10.10.40",
        is_retry=True,
        error_type=None
    )
    mock_generate_command.return_value = GraphState(
        query="Conduct a full port scan on IP 10.10.10.40",
        context={},
        act_result=act_result,
        processed_query="scan all ports on 10.10.10.40",
        command_candidates=["nmap -sS -p- 10.10.10.40"],
        is_retry=True,
        error_type=None
    )
    mock_modify_command.return_value = GraphState(
        query="Conduct a full port scan on IP 10.10.10.40",
        context={},
        act_result=act_result,
        processed_query="scan all ports on 10.10.10.40",
        command_candidates=["nmap -sS -p- 10.10.10.40"],
        is_retry=True,
        error_type=None
    )
    mock_format_result.return_value = GraphState(
        query="Conduct a full port scan on IP 10.10.10.40",
        context={},
        act_result=act_result,
        processed_query="scan all ports on 10.10.10.40",
        command_candidates=["nmap -sS -p- 10.10.10.40"],
        generated_command=GeneratedCommand(
            command="nmap -sS -p- 10.10.10.40",
            explanation="This command performs a SYN scan on all ports."
        ),
        is_retry=True,
        error_type=None
    )

    # Create the initial state with feedback
    initial_state = GraphState(
        query="Conduct a full port scan on IP 10.10.10.40",
        context={},
        act_result=act_result
    )

    # Create the graph
    graph = create_command_generation_graph(settings_obj=settings)

    # Act
    # Use dict() to ensure we get a proper dictionary instead of AddableValuesDict
    result = dict(graph.invoke(initial_state))

    # Assert
    # Verify that the nodes were called in the correct order
    mock_analyze_feedback.assert_called_once()
    mock_process_query.assert_called_once()  # For unknown errors, follow the normal flow
    mock_generate_command.assert_called_once()
    mock_modify_command.assert_called_once()
    mock_format_result.assert_called_once()

    # Verify the result
    assert result["generated_command"].command == "nmap -sS -p- 10.10.10.40"
    assert "SYN scan" in result["generated_command"].explanation
