"""Unit tests for the feedback analyzer node."""

from unittest.mock import MagicMock

import pytest
from wish_models.command_result import CommandState
from wish_models.test_factories.command_input_factory import CommandInputFactory
from wish_models.test_factories.command_result_factory import CommandResultSuccessFactory
from wish_models.test_factories.settings_factory import SettingsFactory

from wish_command_generation_api.nodes import feedback_analyzer
from wish_command_generation_api.test_factories.graph_state_factory import GraphStateFactory


@pytest.fixture
def settings():
    """Create a settings object for testing."""
    return SettingsFactory()


def test_analyze_feedback_no_feedback(settings):
    """Test analyzing feedback when no feedback is provided."""
    # Arrange
    state = GraphStateFactory(query="test query", context={})

    # Act
    result = feedback_analyzer.analyze_feedback(state, settings)

    # Assert
    assert result.is_retry is False
    assert result.error_type is None
    assert result.failed_command_results is None


def test_analyze_feedback_timeout(settings):
    """Test analyzing feedback with a TIMEOUT error."""
    # Arrange
    timeout_result = CommandResultSuccessFactory(
        state=CommandState.TIMEOUT,
        exit_code=1,
        log_summary="timeout",
    )
    state = GraphStateFactory.create_with_feedback("test query", [timeout_result])

    # Act
    result = feedback_analyzer.analyze_feedback(state, settings)

    # Assert
    assert result.is_retry is True
    assert result.error_type == "TIMEOUT"
    assert result.failed_command_results == [timeout_result]


def test_analyze_feedback_network_error(settings):
    """Test analyzing feedback with a NETWORK_ERROR."""
    # Arrange
    network_error_result = CommandResultSuccessFactory(
        state=CommandState.NETWORK_ERROR,
        exit_code=1,
        log_summary="network error",
    )
    state = GraphStateFactory.create_with_feedback("test query", [network_error_result])

    # Act
    result = feedback_analyzer.analyze_feedback(state, settings)

    # Assert
    assert result.is_retry is True
    assert result.error_type == "NETWORK_ERROR"
    assert result.failed_command_results == [network_error_result]


def test_analyze_feedback_multiple_errors(settings):
    """Test analyzing feedback with multiple errors, should prioritize TIMEOUT."""
    # Arrange
    success_result = CommandResultSuccessFactory(
        num=1,
        state=CommandState.SUCCESS,
        exit_code=0,
        log_summary="success",
    )
    network_error_result = CommandResultSuccessFactory(
        num=2,
        state=CommandState.NETWORK_ERROR,
        exit_code=1,
        log_summary="network error",
    )
    timeout_result = CommandResultSuccessFactory(
        num=3,
        state=CommandState.TIMEOUT,
        exit_code=1,
        log_summary="timeout",
    )

    act_results = [success_result, network_error_result, timeout_result]
    state = GraphStateFactory.create_with_feedback("test query", act_results)

    # Act
    result = feedback_analyzer.analyze_feedback(state, settings)

    # Assert
    assert result.is_retry is True
    assert result.error_type == "TIMEOUT"  # TIMEOUT should be prioritized
    assert result.failed_command_results == act_results


def test_analyze_feedback_exception_propagation(settings):
    """Test that exceptions are propagated during feedback analysis."""
    # Arrange
    state = MagicMock()
    state.failed_command_results = MagicMock(side_effect=Exception("Test error"))

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
        CommandInputFactory(command="ls -la", timeout_sec=60),
        CommandInputFactory(command="find . -name '*.py'", timeout_sec=60)
    ]
    timeout_result = CommandResultSuccessFactory(
        state=CommandState.TIMEOUT,
        exit_code=1,
        log_summary="timeout",
    )

    state = GraphStateFactory(
        query="test query",
        context={"current_directory": "/home/user"},
        processed_query=processed_query,
        command_candidates=command_candidates,
        failed_command_results=[timeout_result]
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
    assert result.failed_command_results == [timeout_result]
