"""Tests for analyzer.py."""

from unittest.mock import MagicMock, patch

import pytest
from wish_models.command_result.command_state import CommandState

from wish_log_analysis.analyzer import LogAnalyzer
from wish_log_analysis.test_factories import CommandResultFactory


@pytest.fixture
def mock_graph():
    """Mock the graph used in LogAnalyzer."""
    with patch("wish_log_analysis.analyzer.create_log_analysis_graph") as mock_create_graph:
        # Set up the mock graph
        mock_graph = MagicMock()
        mock_create_graph.return_value = mock_graph

        yield mock_graph


def test_analyze_result(mock_graph):
    """Test that analyze_result calls the graph with the correct arguments and returns the result."""
    # Create a command result
    command_result = CommandResultFactory()

    # Set up the mock graph to return a command result
    analyzed_command_result = CommandResultFactory(
        command=command_result.command,
        exit_code=command_result.exit_code,
        log_files=command_result.log_files,
        log_summary="This is a log summary",
        state=CommandState.SUCCESS
    )
    mock_graph.invoke.return_value = {"analyzed_command_result": analyzed_command_result}

    # Create a log analyzer
    analyzer = LogAnalyzer()

    # Analyze the command result
    result = analyzer.analyze_result(command_result)

    # Check that the graph was called with the correct arguments
    mock_graph.invoke.assert_called_once()
    args = mock_graph.invoke.call_args[0][0]
    assert args["command_result"] == command_result

    # Check that the result is correct
    assert result == analyzed_command_result
