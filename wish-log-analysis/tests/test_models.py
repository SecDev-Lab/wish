"""Tests for models.py."""

from wish_models.command_result.command_state import CommandState

from wish_log_analysis.models import GraphState
from wish_log_analysis.test_factories import CommandResultFactory


def test_graph_state_creation():
    """Test that a GraphState can be created."""
    # Create a command result
    command_result = CommandResultFactory()

    # Create a graph state
    graph_state = GraphState(command_result=command_result)

    # Check that the graph state was created correctly
    assert graph_state.command_result == command_result
    assert graph_state.log_summary is None
    assert graph_state.command_state is None
    assert graph_state.analyzed_command_result is None


def test_graph_state_with_log_summary():
    """Test that a GraphState can be created with a log summary."""
    # Create a command result
    command_result = CommandResultFactory()

    # Create a graph state with a log summary
    log_summary = "This is a log summary"
    graph_state = GraphState(command_result=command_result, log_summary=log_summary)

    # Check that the graph state was created correctly
    assert graph_state.command_result == command_result
    assert graph_state.log_summary == log_summary
    assert graph_state.command_state is None
    assert graph_state.analyzed_command_result is None


def test_graph_state_with_command_state():
    """Test that a GraphState can be created with a command state."""
    # Create a command result
    command_result = CommandResultFactory()

    # Create a graph state with a command state
    command_state = CommandState.SUCCESS
    graph_state = GraphState(command_result=command_result, command_state=command_state)

    # Check that the graph state was created correctly
    assert graph_state.command_result == command_result
    assert graph_state.log_summary is None
    assert graph_state.command_state == command_state
    assert graph_state.analyzed_command_result is None


def test_graph_state_with_analyzed_command_result():
    """Test that a GraphState can be created with an analyzed command result."""
    # Create a command result
    command_result = CommandResultFactory()

    # Create an analyzed command result
    analyzed_command_result = CommandResultFactory()

    # Create a graph state with an analyzed command result
    graph_state = GraphState(
        command_result=command_result,
        analyzed_command_result=analyzed_command_result
    )

    # Check that the graph state was created correctly
    assert graph_state.command_result == command_result
    assert graph_state.log_summary is None
    assert graph_state.command_state is None
    assert graph_state.analyzed_command_result == analyzed_command_result


def test_graph_state_complete():
    """Test that a GraphState can be created with all fields set."""
    # Create a command result
    command_result = CommandResultFactory()

    # Create an analyzed command result
    analyzed_command_result = CommandResultFactory()

    # Create a graph state with all fields set
    log_summary = "This is a log summary"
    command_state = CommandState.SUCCESS
    graph_state = GraphState(
        command_result=command_result,
        log_summary=log_summary,
        command_state=command_state,
        analyzed_command_result=analyzed_command_result
    )

    # Check that the graph state was created correctly
    assert graph_state.command_result == command_result
    assert graph_state.log_summary == log_summary
    assert graph_state.command_state == command_state
    assert graph_state.analyzed_command_result == analyzed_command_result
