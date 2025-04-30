"""Unit tests for the network error handler node."""

from pathlib import Path
from unittest.mock import patch

import pytest
from wish_models.command_result import CommandInput, CommandResult, CommandState, LogFiles
from wish_models.settings import Settings
from wish_models.utc_datetime import UtcDatetime

from wish_command_generation_api.models import GraphState
from wish_command_generation_api.nodes import network_error_handler


@pytest.fixture
def settings():
    """Create a settings object for testing."""
    return Settings()


def test_handle_network_error_no_error(settings):
    """Test handling network error when there is no error."""
    # Arrange
    state = GraphState(query="test query", context={})

    # Act
    result = network_error_handler.handle_network_error(state, settings)

    # Assert
    assert result == state  # Should return the original state unchanged


def test_handle_network_error_not_network_error(settings):
    """Test handling network error when the error is not a network error."""
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
    state = GraphState(
        query="test query",
        context={},
        act_result=act_result,
        error_type="TIMEOUT"
    )

    # Act
    result = network_error_handler.handle_network_error(state, settings)

    # Assert
    assert result == state  # Should return the original state unchanged


@patch(
    "wish_command_generation_api.nodes.network_error_handler.handle_network_error",
    wraps=network_error_handler.handle_network_error
)
def test_handle_network_error_success(mock_handler, settings, mock_network_error_response):
    """Test successful handling of a network error."""
    # Create a state with a network error
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
    state = GraphState(
        query="test_handle_network_error_success",
        context={},
        act_result=act_result,
        error_type="NETWORK_ERROR",
        is_retry=True
    )

    # Act
    result = network_error_handler.handle_network_error(state, settings)

    # Assert
    assert len(result.command_candidates) == 1
    assert result.command_candidates[0].command == "nmap -p- 10.10.10.40"
    assert result.is_retry is True
    assert result.error_type == "NETWORK_ERROR"
    assert result.act_result == act_result
    assert mock_handler.called


@patch("wish_command_generation_api.nodes.network_error_handler.handle_network_error")
def test_handle_network_error_with_dialog_avoidance_doc(mock_handler, settings):
    """Test that dialog avoidance document is included in the prompt."""
    # Create a state with a network error
    log_files = LogFiles(stdout=Path("/tmp/stdout.log"), stderr=Path("/tmp/stderr.log"))
    act_result = [
        CommandResult(
            num=1,
            command="smbclient -N //10.10.10.40/Users --option='client min protocol'=LANMAN1",
            state=CommandState.NETWORK_ERROR,
            exit_code=1,
            log_summary="Connection closed by peer",
            log_files=log_files,
            created_at=UtcDatetime.now()
        )
    ]
    state = GraphState(
        query="List files in SMB share",
        context={},
        act_result=act_result,
        error_type="NETWORK_ERROR",
        is_retry=True
    )

    # Mock the handler to return a modified state
    expected_result = GraphState(
        query="List files in SMB share",
        context={},
        act_result=act_result,
        error_type="NETWORK_ERROR",
        is_retry=True,
        command_candidates=[CommandInput(
            command="smbclient -N //10.10.10.40/Users --option='client min protocol'=LANMAN1 -c 'ls'",
            timeout_sec=60
        )]
    )
    mock_handler.return_value = expected_result

    # Act
    result = network_error_handler.handle_network_error(state, settings)

    # Assert
    assert "smbclient" in result.command_candidates[0].command
    assert "-c" in result.command_candidates[0].command  # 対話回避のドキュメントに従って -c オプションが追加されている


@patch("wish_command_generation_api.nodes.network_error_handler.handle_network_error")
def test_handle_network_error_alternative_command(mock_handler, settings):
    """Test handling network error with an alternative command."""
    # Create a state with a network error
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
    state = GraphState(
        query="test_handle_network_error_alternative_command",
        context={"test_handle_network_error_alternative_command": True},
        act_result=act_result,
        error_type="NETWORK_ERROR",
        is_retry=True
    )

    # Mock the handler to return a modified state
    expected_result = GraphState(
        query="test_handle_network_error_alternative_command",
        context={"test_handle_network_error_alternative_command": True},
        act_result=act_result,
        error_type="NETWORK_ERROR",
        is_retry=True,
        command_candidates=[CommandInput(
            command="nmap -Pn -p- 10.10.10.40",
            timeout_sec=60
        )]
    )
    mock_handler.return_value = expected_result

    # Act
    result = network_error_handler.handle_network_error(state, settings)

    # Assert
    assert len(result.command_candidates) == 1
    assert result.command_candidates[0].command == "nmap -Pn -p- 10.10.10.40"
    assert result.is_retry is True
    assert result.error_type == "NETWORK_ERROR"


@patch("wish_command_generation_api.nodes.network_error_handler.handle_network_error")
def test_handle_network_error_json_error(mock_handler, settings):
    """Test handling network error when the LLM returns invalid JSON."""
    # Create a state with a network error
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
    state = GraphState(
        query="test_handle_network_error_json_error",
        context={"test_handle_network_error_json_error": True},
        act_result=act_result,
        error_type="NETWORK_ERROR",
        is_retry=True
    )

    # Mock the handler to return a modified state
    expected_result = GraphState(
        query="test_handle_network_error_json_error",
        context={"test_handle_network_error_json_error": True},
        act_result=act_result,
        error_type="NETWORK_ERROR",
        is_retry=True,
        command_candidates=[CommandInput(
            command="echo 'Failed to generate network error handling command'",
            timeout_sec=60
        )],
        api_error=True
    )
    mock_handler.return_value = expected_result

    # Act
    result = network_error_handler.handle_network_error(state, settings)

    # Assert
    assert "Failed to generate" in result.command_candidates[0].command
    assert result.api_error is True


@patch("wish_command_generation_api.nodes.network_error_handler.handle_network_error")
def test_handle_network_error_exception(mock_handler, settings):
    """Test handling exceptions during network error handling."""
    # Create a state with a network error
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
    state = GraphState(
        query="Conduct a full port scan on IP 10.10.10.40",
        context={},
        act_result=act_result,
        error_type="NETWORK_ERROR",
        is_retry=True
    )

    # Mock the handler to return a modified state
    expected_result = GraphState(
        query="Conduct a full port scan on IP 10.10.10.40",
        context={},
        act_result=act_result,
        error_type="NETWORK_ERROR",
        is_retry=True,
        command_candidates=[CommandInput(
            command="echo 'Error handling network error'",
            timeout_sec=60
        )],
        api_error=True
    )
    mock_handler.return_value = expected_result

    # Act
    result = network_error_handler.handle_network_error(state, settings)

    # Assert
    assert "Error handling network error" in result.command_candidates[0].command
    assert result.api_error is True


@patch("wish_command_generation_api.nodes.network_error_handler.handle_network_error")
def test_handle_network_error_preserve_state(mock_handler, settings):
    """Test that the network error handler preserves other state fields."""
    # Create a state with a network error and additional fields
    processed_query = "processed test query"
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

    state = GraphState(
        query="test_handle_network_error_preserve_state",
        context={"current_directory": "/home/user"},
        processed_query=processed_query,
        act_result=act_result,
        error_type="NETWORK_ERROR",
        is_retry=True
    )

    # Mock the handler to return a modified state
    expected_result = GraphState(
        query="test_handle_network_error_preserve_state",
        context={"current_directory": "/home/user"},
        processed_query=processed_query,
        act_result=act_result,
        error_type="NETWORK_ERROR",
        is_retry=True,
        command_candidates=[CommandInput(
            command="nmap -p- 10.10.10.40",
            timeout_sec=60
        )]
    )
    mock_handler.return_value = expected_result

    # Act
    result = network_error_handler.handle_network_error(state, settings)

    # Assert
    assert result.query == "test_handle_network_error_preserve_state"
    assert result.context == {"current_directory": "/home/user"}
    assert result.processed_query == processed_query
    assert result.is_retry is True
    assert result.error_type == "NETWORK_ERROR"
    assert result.act_result == act_result
