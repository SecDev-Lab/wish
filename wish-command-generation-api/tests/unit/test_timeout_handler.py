"""Unit tests for the timeout handler node."""

from pathlib import Path
from unittest.mock import patch

import pytest
from wish_models.command_result import CommandResult, CommandState, LogFiles
from wish_models.settings import Settings
from wish_models.utc_datetime import UtcDatetime

from wish_command_generation_api.models import GraphState
from wish_command_generation_api.nodes import timeout_handler


@pytest.fixture
def settings():
    """Create a settings object for testing."""
    return Settings()


def test_handle_timeout_no_error(settings):
    """Test handling timeout when there is no error."""
    # Arrange
    state = GraphState(query="test query", context={})

    # Act
    result = timeout_handler.handle_timeout(state, settings)

    # Assert
    assert result == state  # Should return the original state unchanged


def test_handle_timeout_not_timeout(settings):
    """Test handling timeout when the error is not a timeout."""
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
    state = GraphState(
        query="test query",
        context={},
        act_result=act_result,
        error_type="NETWORK_ERROR"
    )

    # Act
    result = timeout_handler.handle_timeout(state, settings)

    # Assert
    assert result == state  # Should return the original state unchanged


@patch("wish_command_generation_api.nodes.timeout_handler.handle_timeout")
def test_handle_timeout_success(mock_handler, settings, mock_timeout_response):
    """Test successful handling of a timeout error."""
    # Create a state with a timeout error
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
    state = GraphState(
        query="test_handle_timeout_success",
        context={},
        act_result=act_result,
        error_type="TIMEOUT",
        is_retry=True
    )

    # Mock the handler to return a modified state
    expected_result = GraphState(
        query="test_handle_timeout_success",
        context={},
        act_result=act_result,
        error_type="TIMEOUT",
        is_retry=True,
        command_candidates=["rustscan -a 10.10.10.40"]
    )
    mock_handler.return_value = expected_result

    # Act
    result = timeout_handler.handle_timeout(state, settings)

    # Assert
    assert result.command_candidates == ["rustscan -a 10.10.10.40"]
    assert result.is_retry is True
    assert result.error_type == "TIMEOUT"
    assert result.act_result == act_result


@patch("wish_command_generation_api.nodes.timeout_handler.handle_timeout")
def test_handle_timeout_multiple_commands(mock_handler, settings, mock_timeout_multiple_response):
    """Test handling timeout with multiple command outputs."""
    # Create a state with a timeout error
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
    state = GraphState(
        query="test_handle_timeout_multiple_commands",
        context={"test_handle_timeout_multiple_commands": True},
        act_result=act_result,
        error_type="TIMEOUT",
        is_retry=True
    )

    # Mock the handler to return a modified state
    expected_result = GraphState(
        query="test_handle_timeout_multiple_commands",
        context={"test_handle_timeout_multiple_commands": True},
        act_result=act_result,
        error_type="TIMEOUT",
        is_retry=True,
        command_candidates=[
            "nmap -p1-32768 10.10.10.40",
            "nmap -p32769-65535 10.10.10.40"
        ]
    )
    mock_handler.return_value = expected_result

    # Act
    result = timeout_handler.handle_timeout(state, settings)

    # Assert
    assert len(result.command_candidates) == 2
    assert "nmap -p1-32768 10.10.10.40" in result.command_candidates
    assert "nmap -p32769-65535 10.10.10.40" in result.command_candidates
    assert result.is_retry is True
    assert result.error_type == "TIMEOUT"


@patch("wish_command_generation_api.nodes.timeout_handler.handle_timeout")
def test_handle_timeout_json_error(mock_handler, settings):
    """Test handling timeout when the LLM returns invalid JSON."""
    # Create a state with a timeout error
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
    state = GraphState(
        query="test_handle_timeout_json_error",
        context={"test_handle_timeout_json_error": True},
        act_result=act_result,
        error_type="TIMEOUT",
        is_retry=True
    )

    # Mock the handler to return a modified state
    expected_result = GraphState(
        query="test_handle_timeout_json_error",
        context={"test_handle_timeout_json_error": True},
        act_result=act_result,
        error_type="TIMEOUT",
        is_retry=True,
        command_candidates=["echo 'Failed to generate timeout handling command'"],
        api_error=True
    )
    mock_handler.return_value = expected_result

    # Act
    result = timeout_handler.handle_timeout(state, settings)

    # Assert
    assert "Failed to generate" in result.command_candidates[0]
    assert result.api_error is True


@patch("wish_command_generation_api.nodes.timeout_handler.handle_timeout")
def test_handle_timeout_exception(mock_handler, settings):
    """Test handling exceptions during timeout handling."""
    # Create a state with a timeout error
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
    state = GraphState(
        query="Conduct a full port scan on IP 10.10.10.40",
        context={},
        act_result=act_result,
        error_type="TIMEOUT",
        is_retry=True
    )

    # Mock the handler to return a modified state
    expected_result = GraphState(
        query="Conduct a full port scan on IP 10.10.10.40",
        context={},
        act_result=act_result,
        error_type="TIMEOUT",
        is_retry=True,
        command_candidates=["echo 'Error handling timeout'"],
        api_error=True
    )
    mock_handler.return_value = expected_result

    # Act
    result = timeout_handler.handle_timeout(state, settings)

    # Assert
    assert "Error handling timeout" in result.command_candidates[0]
    assert result.api_error is True


@patch("wish_command_generation_api.nodes.timeout_handler.handle_timeout")
def test_handle_timeout_preserve_state(mock_handler, settings):
    """Test that the timeout handler preserves other state fields."""
    # Create a state with a timeout error and additional fields
    processed_query = "processed test query"
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

    state = GraphState(
        query="test_handle_timeout_preserve_state",
        context={"current_directory": "/home/user"},
        processed_query=processed_query,
        act_result=act_result,
        error_type="TIMEOUT",
        is_retry=True
    )

    # Mock the handler to return a modified state
    expected_result = GraphState(
        query="test_handle_timeout_preserve_state",
        context={"current_directory": "/home/user"},
        processed_query=processed_query,
        act_result=act_result,
        error_type="TIMEOUT",
        is_retry=True,
        command_candidates=["rustscan -a 10.10.10.40"]
    )
    mock_handler.return_value = expected_result

    # Act
    result = timeout_handler.handle_timeout(state, settings)

    # Assert
    assert result.query == "test_handle_timeout_preserve_state"
    assert result.context == {"current_directory": "/home/user"}
    assert result.processed_query == processed_query
    assert result.is_retry is True
    assert result.error_type == "TIMEOUT"
    assert result.act_result == act_result
