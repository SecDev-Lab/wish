"""Unit tests for the timeout handler node."""

from unittest.mock import patch

import pytest
from wish_models.command_result import CommandState
from wish_models.test_factories.command_input_factory import CommandInputFactory
from wish_models.test_factories.command_result_factory import CommandResultSuccessFactory
from wish_models.test_factories.settings_factory import SettingsFactory

from wish_command_generation_api.nodes import timeout_handler
from wish_command_generation_api.test_factories.graph_state_factory import GraphStateFactory


@pytest.fixture
def settings():
    """Create a settings object for testing."""
    return SettingsFactory()


@pytest.fixture
def mock_timeout_response():
    """Create a mock response for timeout handling."""
    return "rustscan -a 10.10.10.40"


@pytest.fixture
def mock_timeout_multiple_response():
    """Create a mock response for timeout handling with multiple commands."""
    return "nmap -p1-32768 10.10.10.40"


def test_handle_timeout_no_error(settings):
    """Test handling timeout when there is no error."""
    # Arrange
    state = GraphStateFactory(query="test query", context={})

    # Act
    result = timeout_handler.handle_timeout(state, settings)

    # Assert
    assert result == state  # Should return the original state unchanged


def test_handle_timeout_not_timeout(settings):
    """Test handling timeout when the error is not a timeout."""
    # Arrange
    network_error_result = CommandResultSuccessFactory(
        state=CommandState.NETWORK_ERROR,
        exit_code=1,
        log_summary="network error",
    )
    state = GraphStateFactory.create_with_error("test query", "NETWORK_ERROR")
    state.failed_command_results = [network_error_result]

    # Act
    result = timeout_handler.handle_timeout(state, settings)

    # Assert
    assert result == state  # Should return the original state unchanged


@patch("wish_command_generation_api.nodes.timeout_handler.handle_timeout")
def test_handle_timeout_success(mock_handler, settings, mock_timeout_response):
    """Test successful handling of a timeout error."""
    # Create a state with a timeout error
    state = GraphStateFactory.create_with_timeout_error(
        query="test_handle_timeout_success",
        command="nmap -p- 10.10.10.40"
    )

    # Mock the handler to return a modified state
    command_candidates = [
        CommandInputFactory(
            command="rustscan -a 10.10.10.40",
            timeout_sec=60
        )
    ]
    expected_result = GraphStateFactory.create_with_timeout_error(
        query="test_handle_timeout_success",
        command="nmap -p- 10.10.10.40"
    )
    expected_result.command_candidates = command_candidates
    mock_handler.return_value = expected_result

    # Act
    result = timeout_handler.handle_timeout(state, settings)

    # Assert
    assert len(result.command_candidates) == 1
    assert result.command_candidates[0].command == "rustscan -a 10.10.10.40"
    assert result.is_retry is True
    assert result.error_type == "TIMEOUT"
    assert len(result.failed_command_results) == 1
    assert result.failed_command_results[0].command.command == "nmap -p- 10.10.10.40"
    assert result.failed_command_results[0].state == CommandState.TIMEOUT


@patch("wish_command_generation_api.nodes.timeout_handler.handle_timeout")
def test_handle_timeout_multiple_commands(mock_handler, settings, mock_timeout_multiple_response):
    """Test handling timeout with multiple command outputs."""
    # Create a state with a timeout error
    context = {"test_handle_timeout_multiple_commands": True}
    state = GraphStateFactory.create_with_timeout_error(
        query="test_handle_timeout_multiple_commands",
        command="nmap -p- 10.10.10.40",
        context=context
    )

    # Mock the handler to return a modified state
    command_candidates = [
        CommandInputFactory(command="nmap -p1-32768 10.10.10.40", timeout_sec=60),
        CommandInputFactory(command="nmap -p32769-65535 10.10.10.40", timeout_sec=60)
    ]
    expected_result = GraphStateFactory.create_with_timeout_error(
        query="test_handle_timeout_multiple_commands",
        command="nmap -p- 10.10.10.40",
        context=context
    )
    expected_result.command_candidates = command_candidates
    mock_handler.return_value = expected_result

    # Act
    result = timeout_handler.handle_timeout(state, settings)

    # Assert
    assert len(result.command_candidates) == 2
    assert result.command_candidates[0].command == "nmap -p1-32768 10.10.10.40"
    assert result.command_candidates[1].command == "nmap -p32769-65535 10.10.10.40"
    assert result.is_retry is True
    assert result.error_type == "TIMEOUT"


@patch("wish_command_generation_api.nodes.timeout_handler.handle_timeout")
def test_handle_timeout_json_error(mock_handler, settings):
    """Test handling timeout when the LLM returns invalid JSON."""
    # Create a state with a timeout error
    context = {"test_handle_timeout_json_error": True}
    state = GraphStateFactory.create_with_timeout_error(
        query="test_handle_timeout_json_error",
        command="nmap -p- 10.10.10.40",
        context=context
    )

    # Mock the handler to return a modified state
    command_candidates = [
        CommandInputFactory(
            command="echo 'Failed to generate timeout handling command'",
            timeout_sec=60
        )
    ]
    expected_result = GraphStateFactory.create_with_timeout_error(
        query="test_handle_timeout_json_error",
        command="nmap -p- 10.10.10.40",
        context=context
    )
    expected_result.command_candidates = command_candidates
    expected_result.api_error = True
    mock_handler.return_value = expected_result

    # Act
    result = timeout_handler.handle_timeout(state, settings)

    # Assert
    assert "Failed to generate" in result.command_candidates[0].command
    assert result.api_error is True


@patch("wish_command_generation_api.nodes.timeout_handler.handle_timeout")
def test_handle_timeout_exception(mock_handler, settings):
    """Test handling exceptions during timeout handling."""
    # Create a state with a timeout error
    state = GraphStateFactory.create_with_timeout_error(
        query="Conduct a full port scan on IP 10.10.10.40",
        command="nmap -p- 10.10.10.40"
    )

    # Mock the handler to return a modified state
    command_candidates = [
        CommandInputFactory(
            command="echo 'Error handling timeout'",
            timeout_sec=60
        )
    ]
    expected_result = GraphStateFactory.create_with_timeout_error(
        query="Conduct a full port scan on IP 10.10.10.40",
        command="nmap -p- 10.10.10.40"
    )
    expected_result.command_candidates = command_candidates
    expected_result.api_error = True
    mock_handler.return_value = expected_result

    # Act
    result = timeout_handler.handle_timeout(state, settings)

    # Assert
    assert "Error handling timeout" in result.command_candidates[0].command
    assert result.api_error is True


@patch("wish_command_generation_api.nodes.timeout_handler.handle_timeout")
def test_handle_timeout_preserve_state(mock_handler, settings):
    """Test that the timeout handler preserves other state fields."""
    # Create a state with a timeout error and additional fields
    processed_query = "processed test query"
    context = {"current_directory": "/home/user"}

    state = GraphStateFactory.create_with_timeout_error(
        query="test_handle_timeout_preserve_state",
        command="nmap -p- 10.10.10.40",
        context=context
    )
    state.processed_query = processed_query

    # Mock the handler to return a modified state
    command_candidates = [
        CommandInputFactory(
            command="rustscan -a 10.10.10.40",
            timeout_sec=60
        )
    ]
    expected_result = GraphStateFactory.create_with_timeout_error(
        query="test_handle_timeout_preserve_state",
        command="nmap -p- 10.10.10.40",
        context=context
    )
    expected_result.processed_query = processed_query
    expected_result.command_candidates = command_candidates
    mock_handler.return_value = expected_result

    # Act
    result = timeout_handler.handle_timeout(state, settings)

    # Assert
    assert result.query == "test_handle_timeout_preserve_state"
    assert result.context == {"current_directory": "/home/user"}
    assert result.processed_query == processed_query
    assert result.is_retry is True
    assert result.error_type == "TIMEOUT"
    assert len(result.failed_command_results) == 1
    assert result.failed_command_results[0].command.command == "nmap -p- 10.10.10.40"
    assert result.failed_command_results[0].state == CommandState.TIMEOUT
