"""Unit tests for the network error handler node with mocks."""

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


@patch("wish_command_generation_api.nodes.network_error_handler.handle_network_error")
def test_handle_network_error_success_mock(mock_handler, settings):
    """Test successful handling of a network error with a mock."""
    # Arrange
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
            command="nmap -p- 10.10.10.40",
            timeout_sec=60
        )]
    )
    mock_handler.return_value = expected_result

    # Act
    result = network_error_handler.handle_network_error(state, settings)

    # Assert
    assert len(result.command_candidates) == 1
    assert result.command_candidates[0].command == "nmap -p- 10.10.10.40"
    assert result.is_retry is True
    assert result.error_type == "NETWORK_ERROR"
    assert result.act_result == act_result
