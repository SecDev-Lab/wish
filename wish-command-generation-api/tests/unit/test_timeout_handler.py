"""Unit tests for the timeout handler node."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

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


@patch("langchain_openai.ChatOpenAI")
def test_handle_timeout_success(mock_chat, settings, mock_timeout_response):
    """Test successful handling of a timeout error."""
    # Arrange
    # Mock the LLM and chain
    mock_instance = MagicMock()
    mock_chain = MagicMock()
    mock_instance.__or__.return_value = mock_chain
    mock_chat.return_value = mock_instance

    # Mock the LLM response
    mock_chain.invoke.return_value = mock_timeout_response

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

    # Act
    result = timeout_handler.handle_timeout(state, settings)

    # Assert
    assert result.command_candidates == ["rustscan -a 10.10.10.40"]
    assert result.is_retry is True
    assert result.error_type == "TIMEOUT"
    assert result.act_result == act_result

    # Verify the LLM was called correctly
    mock_chat.assert_called_once()
    mock_chain.invoke.assert_called_once()

    # Check that the prompt includes the necessary documents
    args, _ = mock_chain.invoke.call_args
    prompt_args = args[0]
    assert "高速な代替コマンド案" in str(prompt_args)
    assert "分割統治案" in str(prompt_args)


@patch("langchain_openai.ChatOpenAI")
def test_handle_timeout_multiple_commands(mock_chat, settings, mock_timeout_multiple_response):
    """Test handling timeout with multiple command outputs."""
    # Arrange
    # Mock the LLM and chain
    mock_instance = MagicMock()
    mock_chain = MagicMock()
    mock_instance.__or__.return_value = mock_chain
    mock_chat.return_value = mock_instance

    # Mock the LLM response with multiple commands (divide and conquer)
    mock_chain.invoke.return_value = mock_timeout_multiple_response

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

    # Act
    result = timeout_handler.handle_timeout(state, settings)

    # Assert
    assert len(result.command_candidates) == 2
    assert "nmap -p1-32768 10.10.10.40" in result.command_candidates
    assert "nmap -p32769-65535 10.10.10.40" in result.command_candidates
    assert result.is_retry is True
    assert result.error_type == "TIMEOUT"


@patch("langchain_openai.ChatOpenAI")
def test_handle_timeout_json_error(mock_chat, settings):
    """Test handling timeout when the LLM returns invalid JSON."""
    # Arrange
    # Mock the LLM and chain
    mock_instance = MagicMock()
    mock_chain = MagicMock()
    mock_instance.__or__.return_value = mock_chain
    mock_chat.return_value = mock_instance

    # Mock the LLM response with invalid JSON
    mock_chain.invoke.return_value = "Invalid JSON"

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

    # Act
    with patch("wish_command_generation_api.nodes.timeout_handler.logger") as mock_logger:
        result = timeout_handler.handle_timeout(state, settings)

        # Assert
        assert "Failed to generate" in result.command_candidates[0]
        assert result.api_error is True
        mock_logger.error.assert_called_once()


@patch("langchain_openai.ChatOpenAI")
def test_handle_timeout_exception(mock_chat, settings):
    """Test handling exceptions during timeout handling."""
    # Arrange
    # Mock the LLM to raise an exception
    mock_chat.side_effect = Exception("Test error")

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

    # Act
    with patch("wish_command_generation_api.nodes.timeout_handler.logger") as mock_logger:
        result = timeout_handler.handle_timeout(state, settings)

        # Assert
        assert "Error handling timeout" in result.command_candidates[0]
        assert result.api_error is True
        mock_logger.exception.assert_called_once()


@patch("langchain_openai.ChatOpenAI")
def test_handle_timeout_preserve_state(mock_chat, settings):
    """Test that the timeout handler preserves other state fields."""
    # Arrange
    # Mock the LLM and chain
    mock_instance = MagicMock()
    mock_chain = MagicMock()
    mock_instance.__or__.return_value = mock_chain
    mock_chat.return_value = mock_instance

    # Mock the LLM response
    mock_chain.invoke.return_value = json.dumps({
        "command_inputs": [
            {
                "command": "rustscan -a 10.10.10.40",
                "timeout_sec": 60
            }
        ]
    })

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
        query="Conduct a full port scan on IP 10.10.10.40",
        context={"current_directory": "/home/user"},
        processed_query=processed_query,
        act_result=act_result,
        error_type="TIMEOUT",
        is_retry=True
    )

    # Act
    result = timeout_handler.handle_timeout(state, settings)

    # Assert
    assert result.query == "Conduct a full port scan on IP 10.10.10.40"
    assert result.context == {"current_directory": "/home/user"}
    assert result.processed_query == processed_query
    assert result.command_candidates == ["rustscan -a 10.10.10.40"]
    assert result.is_retry is True
    assert result.error_type == "TIMEOUT"
    assert result.act_result == act_result
