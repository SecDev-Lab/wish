"""Tests for result_combiner.py."""

import pytest
from wish_models.command_result.command_state import CommandState

from wish_log_analysis.nodes.result_combiner import combine_results
from wish_log_analysis.test_factories import CommandResultFactory, GraphStateFactory


def test_combine_results():
    """Test that combine_results combines the results correctly."""
    # Create a command result
    command_result = CommandResultFactory()

    # Create a graph state with log summary and command state
    log_summary = "This is a log summary"
    command_state = CommandState.SUCCESS
    graph_state = GraphStateFactory.create_with_command_result(command_result)
    graph_state.log_summary = log_summary
    graph_state.command_state = command_state

    # Combine the results
    result = combine_results(graph_state)

    # Check that the results were combined correctly
    assert result.analyzed_command_result is not None
    assert result.analyzed_command_result.command == command_result.command
    assert result.analyzed_command_result.exit_code == command_result.exit_code
    assert result.analyzed_command_result.log_files == command_result.log_files
    assert result.analyzed_command_result.log_summary == log_summary
    assert result.analyzed_command_result.state == command_state
    assert result.analyzed_command_result.created_at == command_result.created_at


def test_combine_results_missing_log_summary():
    """Test that combine_results raises an error when log_summary is missing."""
    # Create a command result
    command_result = CommandResultFactory()

    # Create a graph state with command state but no log summary
    command_state = CommandState.SUCCESS
    graph_state = GraphStateFactory.create_with_command_result(command_result)
    graph_state.command_state = command_state

    # Check that combine_results raises a ValueError
    with pytest.raises(ValueError):
        combine_results(graph_state)


def test_combine_results_missing_command_state():
    """Test that combine_results raises an error when command_state is missing."""
    # Create a command result
    command_result = CommandResultFactory()

    # Create a graph state with log summary but no command state
    log_summary = "This is a log summary"
    graph_state = GraphStateFactory.create_with_command_result(command_result)
    graph_state.log_summary = log_summary

    # Check that combine_results raises a ValueError
    with pytest.raises(ValueError):
        combine_results(graph_state)
