"""Unit tests for the feedback analyzer node."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from wish_models.command_result import CommandInput, CommandResult, CommandState, LogFiles
from wish_models.settings import Settings
from wish_models.utc_datetime import UtcDatetime

from wish_command_generation_api.models import GraphState
from wish_command_generation_api.nodes import feedback_analyzer


@pytest.fixture
def settings():
    """Create a settings object for testing."""
    return Settings()


def test_analyze_feedback_no_feedback(settings):
    """Test analyzing feedback when no feedback is provided."""
    # Arrange
    state = GraphState(query="test query", context={})

    # Act
    result = feedback_analyzer.analyze_feedback(state, settings)

    # Assert
    assert result.is_retry is False
    assert result.error_type is None
    assert result.act_result is None


def test_analyze_feedback_timeout(settings):
    """Test analyzing feedback with a TIMEOUT error."""
    # Arrange
    log_files = LogFiles(stdout=Path("/tmp/stdout.log"), stderr=Path("/tmp/stderr.log"))
    act_result = [
        CommandResult(
            num=1,
            command="test command",
            state=CommandState.TIMEOUT,
            exit_code=1,
            log_summary="timeout",
            log_files=log_files,
            created_at=UtcDatetime.now()
        )
    ]
    state = GraphState(query="test query", context={}, act_result=act_result)

    # Act
    result = feedback_analyzer.analyze_feedback(state, settings)

    # Assert
    assert result.is_retry is True
    assert result.error_type == "TIMEOUT"
    assert result.act_result == act_result


def test_analyze_feedback_network_error(settings):
    """Test analyzing feedback with a NETWORK_ERROR."""
    # Arrange
    log_files = LogFiles(stdout=Path("/tmp/stdout.log"), stderr=Path("/tmp/stderr.log"))
    act_result = [
        CommandResult(
            num=1,
            command="test command",
            state=CommandState.NETWORK_ERROR,
            exit_code=1,
            log_summary="network error",
            log_files=log_files,
            created_at=UtcDatetime.now()
        )
    ]
    state = GraphState(query="test query", context={}, act_result=act_result)

    # Act
    result = feedback_analyzer.analyze_feedback(state, settings)

    # Assert
    assert result.is_retry is True
    assert result.error_type == "NETWORK_ERROR"
    assert result.act_result == act_result


def test_analyze_feedback_multiple_errors(settings):
    """Test analyzing feedback with multiple errors, should prioritize TIMEOUT."""
    # Arrange
    log_files = LogFiles(stdout=Path("/tmp/stdout.log"), stderr=Path("/tmp/stderr.log"))
    act_result = [
        CommandResult(
            num=1,
            command="command1",
            state=CommandState.SUCCESS,
            exit_code=0,
            log_summary="success",
            log_files=log_files,
            created_at=UtcDatetime.now()
        ),
        CommandResult(
            num=2,
            command="command2",
            state=CommandState.NETWORK_ERROR,
            exit_code=1,
            log_summary="network error",
            log_files=log_files,
            created_at=UtcDatetime.now()
        ),
        CommandResult(
            num=3,
            command="command3",
            state=CommandState.TIMEOUT,
            exit_code=1,
            log_summary="timeout",
            log_files=log_files,
            created_at=UtcDatetime.now()
        )
    ]
    state = GraphState(query="test query", context={}, act_result=act_result)

    # Act
    result = feedback_analyzer.analyze_feedback(state, settings)

    # Assert
    assert result.is_retry is True
    assert result.error_type == "TIMEOUT"  # TIMEOUT should be prioritized
    assert result.act_result == act_result


def test_analyze_feedback_exception_propagation(settings):
    """Test that exceptions are propagated during feedback analysis."""
    # Arrange
    state = MagicMock()
    state.act_result = MagicMock(side_effect=Exception("Test error"))

    # Act & Assert
    with pytest.raises(Exception) as excinfo:
        feedback_analyzer.analyze_feedback(state, settings)

    # Verify the exception message contains validation error information
    assert "validation errors for GraphState" in str(excinfo.value)


def test_analyze_feedback_preserve_state(settings):
    """Test that the analyzer preserves other state fields."""
    # Arrange
    processed_query = "processed test query"
    command_candidates = [
        CommandInput(command="ls -la", timeout_sec=60),
        CommandInput(command="find . -name '*.py'", timeout_sec=60)
    ]
    log_files = LogFiles(stdout=Path("/tmp/stdout.log"), stderr=Path("/tmp/stderr.log"))
    act_result = [
        CommandResult(
            num=1,
            command="test command",
            state=CommandState.TIMEOUT,
            exit_code=1,
            log_summary="timeout",
            log_files=log_files,
            created_at=UtcDatetime.now()
        )
    ]

    state = GraphState(
        query="test query",
        context={"current_directory": "/home/user"},
        processed_query=processed_query,
        command_candidates=command_candidates,
        act_result=act_result
    )

    # Act
    result = feedback_analyzer.analyze_feedback(state, settings)

    # Assert
    assert result.query == "test query"
    assert result.context == {"current_directory": "/home/user"}
    assert result.processed_query == processed_query
    assert result.command_candidates == command_candidates
    assert result.is_retry is True
    assert result.error_type == "TIMEOUT"
    assert result.act_result == act_result
