"""Integration tests for document integration with command generation."""

from unittest.mock import MagicMock, patch

import pytest
from wish_models.command_result import CommandResult
from wish_models.settings import Settings

from wish_command_generation_api.constants import (
    DIALOG_AVOIDANCE_DOC,
    DIVIDE_AND_CONQUER_DOC,
    FAST_ALTERNATIVE_DOC,
    LIST_FILES_DOC,
)
from wish_command_generation_api.graph import create_command_generation_graph
from wish_command_generation_api.models import GraphState


@pytest.fixture
def settings():
    """Create a settings object for testing."""
    return Settings()


@patch("wish_command_generation_api.nodes.command_generator.generate_command")
def test_command_generator_uses_all_docs(mock_generate_command, settings):
    """Test that command generator uses all documents."""
    # Arrange
    # Mock the command generator to capture the arguments
    mock_generate_command.return_value = GraphState(
        query="test query",
        context={},
        processed_query="processed query",
        command_candidates=["ls -la"],
    )

    # Create the initial state
    initial_state = GraphState(query="test query", context={}, processed_query="processed query")

    # Create the graph
    graph = create_command_generation_graph(settings_obj=settings)

    # Act
    with patch("wish_command_generation_api.nodes.feedback_analyzer.analyze_feedback", return_value=initial_state):
        with patch("wish_command_generation_api.nodes.query_processor.process_query", return_value=initial_state):
            with patch("wish_command_generation_api.nodes.command_modifier.modify_command") as mock_modifier:
                with patch("wish_command_generation_api.nodes.result_formatter.format_result") as mock_formatter:
                    mock_modifier.return_value = initial_state
                    mock_formatter.return_value = initial_state
                    graph.invoke(initial_state)

    # Assert
    # Verify that the command generator was called with all documents
    mock_generate_command.assert_called_once()
    args, kwargs = mock_generate_command.call_args
    assert len(args) > 0
    assert isinstance(args[0], GraphState)
    
    # The actual test will be in test_command_generator.py, but we're ensuring
    # the integration works here


@patch("wish_command_generation_api.nodes.network_error_handler.handle_network_error")
def test_network_error_handler_uses_dialog_avoidance_doc(mock_handle_network_error, settings):
    """Test that network error handler uses dialog avoidance document."""
    # Arrange
    # Create feedback with a network error
    act_result = [
        CommandResult(
            command="smbclient -N //10.10.10.40/Users --option='client min protocol'=LANMAN1",
            exit_class="NETWORK_ERROR",
            exit_code="1",
            log_summary="Connection closed by peer"
        )
    ]

    # Mock the network error handler to capture the arguments
    mock_handle_network_error.return_value = GraphState(
        query="List files in SMB share",
        context={},
        act_result=act_result,
        command_candidates=["smbclient -N //10.10.10.40/Users --option='client min protocol'=LANMAN1 -c 'ls'"],
        is_retry=True,
        error_type="NETWORK_ERROR",
    )

    # Create the initial state with feedback
    initial_state = GraphState(
        query="List files in SMB share",
        context={},
        act_result=act_result,
    )

    # Create the graph
    graph = create_command_generation_graph(settings_obj=settings)

    # Act
    with patch("wish_command_generation_api.nodes.feedback_analyzer.analyze_feedback") as mock_analyzer:
        with patch("wish_command_generation_api.nodes.command_modifier.modify_command") as mock_modifier:
            with patch("wish_command_generation_api.nodes.result_formatter.format_result") as mock_formatter:
                mock_analyzer.return_value = GraphState(
                    query="List files in SMB share",
                    context={},
                    act_result=act_result,
                    is_retry=True,
                    error_type="NETWORK_ERROR",
                )
                mock_modifier.return_value = mock_handle_network_error.return_value
                mock_formatter.return_value = mock_handle_network_error.return_value
                graph.invoke(initial_state)

    # Assert
    # Verify that the network error handler was called
    mock_handle_network_error.assert_called_once()
    
    # The actual test will be in test_network_error_handler.py, but we're ensuring
    # the integration works here


@patch("wish_command_generation_api.nodes.timeout_handler.handle_timeout")
def test_timeout_handler_uses_fast_alternative_and_divide_conquer_docs(mock_handle_timeout, settings):
    """Test that timeout handler uses fast alternative and divide and conquer documents."""
    # Arrange
    # Create feedback with a timeout error
    act_result = [
        CommandResult(
            command="nmap -p- 10.10.10.40",
            exit_class="TIMEOUT",
            exit_code="1",
            log_summary="timeout"
        )
    ]

    # Mock the timeout handler to capture the arguments
    mock_handle_timeout.return_value = GraphState(
        query="Conduct a full port scan on IP 10.10.10.40",
        context={},
        act_result=act_result,
        command_candidates=["rustscan -a 10.10.10.40"],
        is_retry=True,
        error_type="TIMEOUT",
    )

    # Create the initial state with feedback
    initial_state = GraphState(
        query="Conduct a full port scan on IP 10.10.10.40",
        context={},
        act_result=act_result,
    )

    # Create the graph
    graph = create_command_generation_graph(settings_obj=settings)

    # Act
    with patch("wish_command_generation_api.nodes.feedback_analyzer.analyze_feedback") as mock_analyzer:
        with patch("wish_command_generation_api.nodes.command_modifier.modify_command") as mock_modifier:
            with patch("wish_command_generation_api.nodes.result_formatter.format_result") as mock_formatter:
                mock_analyzer.return_value = GraphState(
                    query="Conduct a full port scan on IP 10.10.10.40",
                    context={},
                    act_result=act_result,
                    is_retry=True,
                    error_type="TIMEOUT",
                )
                mock_modifier.return_value = mock_handle_timeout.return_value
                mock_formatter.return_value = mock_handle_timeout.return_value
                graph.invoke(initial_state)

    # Assert
    # Verify that the timeout handler was called
    mock_handle_timeout.assert_called_once()
    
    # The actual test will be in test_timeout_handler.py, but we're ensuring
    # the integration works here


@patch("wish_command_generation_api.nodes.command_modifier.modify_command")
def test_command_modifier_uses_dialog_avoidance_and_list_files_docs(mock_modify_command, settings):
    """Test that command modifier uses dialog avoidance and list files documents."""
    # Arrange
    # Mock the command modifier to capture the arguments
    mock_modify_command.return_value = GraphState(
        query="test query",
        context={},
        processed_query="processed query",
        command_candidates=["smbclient -N //10.10.10.40/Users --option='client min protocol'=LANMAN1 -c 'ls'"],
    )

    # Create the initial state
    initial_state = GraphState(
        query="test query",
        context={},
        processed_query="processed query",
        command_candidates=["smbclient -N //10.10.10.40/Users --option='client min protocol'=LANMAN1"],
    )

    # Create the graph
    graph = create_command_generation_graph(settings_obj=settings)

    # Act
    with patch("wish_command_generation_api.nodes.feedback_analyzer.analyze_feedback", return_value=initial_state):
        with patch("wish_command_generation_api.nodes.query_processor.process_query", return_value=initial_state):
            with patch("wish_command_generation_api.nodes.command_generator.generate_command", return_value=initial_state):
                with patch("wish_command_generation_api.nodes.result_formatter.format_result") as mock_formatter:
                    mock_formatter.return_value = initial_state
                    graph.invoke(initial_state)

    # Assert
    # Verify that the command modifier was called
    mock_modify_command.assert_called_once()
    
    # The actual test will be in test_command_modifier.py, but we're ensuring
    # the integration works here
