"""Unit tests for the feedback analyzer node."""

from unittest.mock import MagicMock, patch

import pytest
from wish_models.command_result import ActResult
from wish_models.settings import Settings

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
    act_result = [ActResult(command="test command", exit_class="TIMEOUT", exit_code="1", log_summary="timeout")]
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
    act_result = [ActResult(command="test command", exit_class="NETWORK_ERROR", exit_code="1", log_summary="network error")]
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
    act_result = [
        ActResult(command="command1", exit_class="SUCCESS", exit_code="0", log_summary="success"),
        ActResult(command="command2", exit_class="NETWORK_ERROR", exit_code="1", log_summary="network error"),
        ActResult(command="command3", exit_class="TIMEOUT", exit_code="1", log_summary="timeout")
    ]
    state = GraphState(query="test query", context={}, act_result=act_result)
    
    # Act
    result = feedback_analyzer.analyze_feedback(state, settings)
    
    # Assert
    assert result.is_retry is True
    assert result.error_type == "TIMEOUT"  # TIMEOUT should be prioritized
    assert result.act_result == act_result


def test_analyze_feedback_exception(settings):
    """Test handling exceptions during feedback analysis."""
    # Arrange
    state = MagicMock()
    state.act_result = MagicMock(side_effect=Exception("Test error"))
    
    # Act
    with patch("wish_command_generation_api.nodes.feedback_analyzer.logger") as mock_logger:
        result = feedback_analyzer.analyze_feedback(state, settings)
        
        # Assert
        assert result.api_error is True
        mock_logger.exception.assert_called_once()


def test_analyze_feedback_preserve_state(settings):
    """Test that the analyzer preserves other state fields."""
    # Arrange
    processed_query = "processed test query"
    command_candidates = ["ls -la", "find . -name '*.py'"]
    act_result = [ActResult(command="test command", exit_class="TIMEOUT", exit_code="1", log_summary="timeout")]
    
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
