"""Unit tests for the network error handler node."""

import json
from unittest.mock import MagicMock, patch

import pytest
from wish_models.command_result import ActResult
from wish_models.settings import Settings

from wish_command_generation_api.constants import DIALOG_AVOIDANCE_DOC
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
    act_result = [ActResult(command="test command", exit_class="TIMEOUT", exit_code="1", log_summary="timeout")]
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


@patch("langchain_openai.ChatOpenAI")
def test_handle_network_error_success(mock_chat, settings):
    """Test successful handling of a network error."""
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
                "command": "nmap -p- 10.10.10.40",
                "timeout_sec": 60
            }
        ]
    })

    # Create a state with a network error
    act_result = [
        ActResult(
            command="nmap -p- 10.10.10.40",
            exit_class="NETWORK_ERROR",
            exit_code="1",
            log_summary="Connection closed by peer"
        )
    ]
    state = GraphState(
        query="Conduct a full port scan on IP 10.10.10.40",
        context={},
        act_result=act_result,
        error_type="NETWORK_ERROR",
        is_retry=True
    )

    # Act
    result = network_error_handler.handle_network_error(state, settings)

    # Assert
    assert result.command_candidates == ["nmap -p- 10.10.10.40"]
    assert result.is_retry is True
    assert result.error_type == "NETWORK_ERROR"
    assert result.act_result == act_result

    # Verify the LLM was called correctly
    mock_chat.assert_called_once()
    mock_chain.invoke.assert_called_once()


@patch("langchain_openai.ChatOpenAI")
def test_handle_network_error_with_dialog_avoidance_doc(mock_chat, settings):
    """Test that dialog avoidance document is included in the prompt."""
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
                "command": "smbclient -N //10.10.10.40/Users --option='client min protocol'=LANMAN1 -c 'ls'",
                "timeout_sec": 60
            }
        ]
    })

    # Create a state with a network error
    act_result = [
        ActResult(
            command="smbclient -N //10.10.10.40/Users --option='client min protocol'=LANMAN1",
            exit_class="NETWORK_ERROR",
            exit_code="1",
            log_summary="Connection closed by peer"
        )
    ]
    state = GraphState(
        query="List files in SMB share",
        context={},
        act_result=act_result,
        error_type="NETWORK_ERROR",
        is_retry=True
    )

    # Act
    result = network_error_handler.handle_network_error(state, settings)

    # Assert
    assert "smbclient" in result.command_candidates[0]
    assert "-c" in result.command_candidates[0]  # 対話回避のドキュメントに従って -c オプションが追加されている

    # Check that the invoke method was called with the dialog_avoidance_doc parameter
    args, kwargs = mock_chain.invoke.call_args
    assert "dialog_avoidance_doc" in kwargs
    assert kwargs["dialog_avoidance_doc"] == DIALOG_AVOIDANCE_DOC


@patch("langchain_openai.ChatOpenAI")
def test_handle_network_error_alternative_command(mock_chat, settings):
    """Test handling network error with an alternative command."""
    # Arrange
    # Mock the LLM and chain
    mock_instance = MagicMock()
    mock_chain = MagicMock()
    mock_instance.__or__.return_value = mock_chain
    mock_chat.return_value = mock_instance

    # Mock the LLM response with an alternative command
    mock_chain.invoke.return_value = json.dumps({
        "command_inputs": [
            {
                "command": "nmap -Pn -p- 10.10.10.40",  # Using -Pn to skip host discovery
                "timeout_sec": 60
            }
        ]
    })

    # Create a state with a network error
    act_result = [
        ActResult(
            command="nmap -p- 10.10.10.40",
            exit_class="NETWORK_ERROR",
            exit_code="1",
            log_summary="Connection closed by peer"
        )
    ]
    state = GraphState(
        query="Conduct a full port scan on IP 10.10.10.40",
        context={},
        act_result=act_result,
        error_type="NETWORK_ERROR",
        is_retry=True
    )

    # Act
    result = network_error_handler.handle_network_error(state, settings)

    # Assert
    assert result.command_candidates == ["nmap -Pn -p- 10.10.10.40"]
    assert result.is_retry is True
    assert result.error_type == "NETWORK_ERROR"


@patch("langchain_openai.ChatOpenAI")
def test_handle_network_error_json_error(mock_chat, settings):
    """Test handling network error when the LLM returns invalid JSON."""
    # Arrange
    # Mock the LLM and chain
    mock_instance = MagicMock()
    mock_chain = MagicMock()
    mock_instance.__or__.return_value = mock_chain
    mock_chat.return_value = mock_instance

    # Mock the LLM response with invalid JSON
    mock_chain.invoke.return_value = "Invalid JSON"

    # Create a state with a network error
    act_result = [
        ActResult(
            command="nmap -p- 10.10.10.40",
            exit_class="NETWORK_ERROR",
            exit_code="1",
            log_summary="Connection closed by peer"
        )
    ]
    state = GraphState(
        query="Conduct a full port scan on IP 10.10.10.40",
        context={},
        act_result=act_result,
        error_type="NETWORK_ERROR",
        is_retry=True
    )

    # Act
    with patch("wish_command_generation_api.nodes.network_error_handler.logger") as mock_logger:
        result = network_error_handler.handle_network_error(state, settings)

        # Assert
        assert "Failed to generate" in result.command_candidates[0]
        assert result.api_error is True
        mock_logger.error.assert_called_once()


@patch("langchain_openai.ChatOpenAI")
def test_handle_network_error_exception(mock_chat, settings):
    """Test handling exceptions during network error handling."""
    # Arrange
    # Mock the LLM to raise an exception
    mock_chat.side_effect = Exception("Test error")

    # Create a state with a network error
    act_result = [
        ActResult(
            command="nmap -p- 10.10.10.40",
            exit_class="NETWORK_ERROR",
            exit_code="1",
            log_summary="Connection closed by peer"
        )
    ]
    state = GraphState(
        query="Conduct a full port scan on IP 10.10.10.40",
        context={},
        act_result=act_result,
        error_type="NETWORK_ERROR",
        is_retry=True
    )

    # Act
    with patch("wish_command_generation_api.nodes.network_error_handler.logger") as mock_logger:
        result = network_error_handler.handle_network_error(state, settings)

        # Assert
        assert "Error handling network error" in result.command_candidates[0]
        assert result.api_error is True
        mock_logger.exception.assert_called_once()


@patch("langchain_openai.ChatOpenAI")
def test_handle_network_error_preserve_state(mock_chat, settings):
    """Test that the network error handler preserves other state fields."""
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
                "command": "nmap -p- 10.10.10.40",
                "timeout_sec": 60
            }
        ]
    })

    # Create a state with a network error and additional fields
    processed_query = "processed test query"
    act_result = [
        ActResult(
            command="nmap -p- 10.10.10.40",
            exit_class="NETWORK_ERROR",
            exit_code="1",
            log_summary="Connection closed by peer"
        )
    ]

    state = GraphState(
        query="Conduct a full port scan on IP 10.10.10.40",
        context={"current_directory": "/home/user"},
        processed_query=processed_query,
        act_result=act_result,
        error_type="NETWORK_ERROR",
        is_retry=True
    )

    # Act
    result = network_error_handler.handle_network_error(state, settings)

    # Assert
    assert result.query == "Conduct a full port scan on IP 10.10.10.40"
    assert result.context == {"current_directory": "/home/user"}
    assert result.processed_query == processed_query
    assert result.command_candidates == ["nmap -p- 10.10.10.40"]
    assert result.is_retry is True
    assert result.error_type == "NETWORK_ERROR"
    assert result.act_result == act_result
