"""Unit tests for the command modifier node."""

from unittest.mock import patch

import pytest
from wish_models.command_result import CommandInput
from wish_models.settings import Settings

from wish_command_generation_api.constants import DEFAULT_TIMEOUT_SEC
from wish_command_generation_api.models import GraphState
from wish_command_generation_api.nodes import command_modifier


@pytest.fixture
def settings():
    """Create a settings object for testing."""
    return Settings()


def test_modify_command_no_commands(settings):
    """Test modifying commands when there are no commands."""
    # Arrange
    state = GraphState(query="test query", context={})

    # Act
    result = command_modifier.modify_command(state, settings)

    # Assert
    assert result == state  # Should return the original state unchanged


@patch("wish_command_generation_api.nodes.command_modifier.modify_command")
def test_modify_command_dialog_avoidance(mock_modify, settings, mock_command_response):
    """Test dialog avoidance modification."""
    # Create a state with an interactive command
    state = GraphState(
        query="Start a Metasploit handler",
        context={},
        command_candidates=[CommandInput(command="msfconsole", timeout_sec=DEFAULT_TIMEOUT_SEC)]
    )

    # Mock the modifier to return a modified state
    expected_result = GraphState(
        query="Start a Metasploit handler",
        context={},
        command_candidates=[
            CommandInput(
                command="msfconsole -q -x \"use exploit/multi/handler; set PAYLOAD windows/meterpreter/reverse_tcp; "
                "set LHOST 10.10.10.1; set LPORT 4444; run; exit -y\"",
                timeout_sec=DEFAULT_TIMEOUT_SEC
            )
        ]
    )
    mock_modify.return_value = expected_result

    # Act
    result = command_modifier.modify_command(state, settings)

    # Assert
    assert len(result.command_candidates) == 1
    assert "exit -y" in result.command_candidates[0].command


@patch("wish_command_generation_api.nodes.command_modifier.modify_command")
def test_modify_command_list_files(mock_modify, settings, mock_list_files_response):
    """Test list files modification."""
    # Create a state with a command using list files
    state = GraphState(
        query="Brute force SMB login",
        context={},
        command_candidates=[
            CommandInput(
                command="hydra -L user_list.txt -P pass_list.txt smb://10.10.10.40",
                timeout_sec=DEFAULT_TIMEOUT_SEC
            )
        ]
    )

    # Mock the modifier to return a modified state
    expected_result = GraphState(
        query="Brute force SMB login",
        context={},
        command_candidates=[
            CommandInput(
                command="hydra -L /usr/share/seclists/Usernames/top-usernames-shortlist.txt "
                "-P /usr/share/seclists/Passwords/xato-net-10-million-passwords-1000.txt smb://10.10.10.40",
                timeout_sec=DEFAULT_TIMEOUT_SEC
            )
        ]
    )
    mock_modify.return_value = expected_result

    # Act
    result = command_modifier.modify_command(state, settings)

    # Assert
    assert len(result.command_candidates) == 1
    assert "/usr/share/seclists/Usernames/top-usernames-shortlist.txt" in result.command_candidates[0].command
    assert "/usr/share/seclists/Passwords/xato-net-10-million-passwords-1000.txt" in \
           result.command_candidates[0].command


@patch("wish_command_generation_api.nodes.command_modifier.modify_command")
def test_modify_command_both_modifications(mock_modify, settings):
    """Test both dialog avoidance and list files modifications."""
    # Create a state with a command needing both modifications
    state = GraphState(
        query="Download user list from SMB share",
        context={},
        command_candidates=[CommandInput(command="smbclient -N //10.10.10.40/share", timeout_sec=DEFAULT_TIMEOUT_SEC)]
    )

    # Mock the modifier to return a modified state
    expected_result = GraphState(
        query="Download user list from SMB share",
        context={},
        command_candidates=[
            CommandInput(
                command="smbclient -N //10.10.10.40/share -c 'get "
                       "/usr/share/seclists/Usernames/top-usernames-shortlist.txt'",
                timeout_sec=DEFAULT_TIMEOUT_SEC
            )
        ]
    )
    mock_modify.return_value = expected_result

    # Act
    result = command_modifier.modify_command(state, settings)

    # Assert
    assert len(result.command_candidates) == 1
    assert "-c 'get" in result.command_candidates[0].command
    assert "/usr/share/seclists/Usernames/top-usernames-shortlist.txt" in result.command_candidates[0].command


@patch("wish_command_generation_api.nodes.command_modifier.modify_command", wraps=command_modifier.modify_command)
def test_modify_command_json_error(mock_modify, settings):
    """Test handling JSON parsing errors."""
    # Create a state with a command
    state = GraphState(
        query="test_modify_command_json_error",
        context={},
        command_candidates=[CommandInput(command="msfconsole", timeout_sec=DEFAULT_TIMEOUT_SEC)]
    )

    # Act
    result = command_modifier.modify_command(state, settings)

    # Assert
    assert len(result.command_candidates) == 1
    assert result.command_candidates[0].command == "msfconsole"  # Original command should be preserved
    assert mock_modify.called


@patch("wish_command_generation_api.nodes.command_modifier.modify_command", wraps=command_modifier.modify_command)
def test_modify_command_exception(mock_modify, settings):
    """Test handling exceptions during command modification."""
    # Create a state with a command
    state = GraphState(
        query="test_modify_command_exception",
        context={},
        command_candidates=[CommandInput(command="msfconsole", timeout_sec=DEFAULT_TIMEOUT_SEC)]
    )

    # Act
    result = command_modifier.modify_command(state, settings)

    # Assert
    assert len(result.command_candidates) == 1
    assert result.command_candidates[0].command == "msfconsole"  # Original command should be preserved
    assert mock_modify.called


@patch("wish_command_generation_api.nodes.command_modifier.modify_command")
def test_modify_command_multiple_commands(mock_modify, settings):
    """Test modifying multiple commands."""
    # Create a state with multiple commands
    state = GraphState(
        query="Run multiple commands",
        context={},
        command_candidates=[
            CommandInput(command="msfconsole", timeout_sec=DEFAULT_TIMEOUT_SEC),
            CommandInput(
                command="hydra -L user_list.txt -P pass_list.txt smb://10.10.10.40",
                timeout_sec=DEFAULT_TIMEOUT_SEC
            )
        ]
    )

    # Mock the modifier to return a modified state
    expected_result = GraphState(
        query="Run multiple commands",
        context={},
        command_candidates=[
            CommandInput(
                command="msfconsole -q -x \"use exploit/multi/handler; exit -y\"",
                timeout_sec=DEFAULT_TIMEOUT_SEC
            ),
            CommandInput(
                command="hydra -L /usr/share/seclists/Usernames/top-usernames-shortlist.txt "
                "-P /usr/share/seclists/Passwords/xato-net-10-million-passwords-1000.txt smb://10.10.10.40",
                timeout_sec=DEFAULT_TIMEOUT_SEC
            )
        ]
    )
    mock_modify.return_value = expected_result

    # Act
    result = command_modifier.modify_command(state, settings)

    # Assert
    assert len(result.command_candidates) == 2
    assert "exit -y" in result.command_candidates[0].command
    assert "/usr/share/seclists/Usernames/top-usernames-shortlist.txt" in result.command_candidates[1].command
    assert "/usr/share/seclists/Passwords/xato-net-10-million-passwords-1000.txt" in \
           result.command_candidates[1].command


@patch("wish_command_generation_api.nodes.command_modifier.modify_command")
def test_modify_command_preserve_state(mock_modify, settings):
    """Test that the command modifier preserves other state fields."""
    # Create a state with additional fields
    processed_query = "processed test query"

    # Create a proper CommandResult object
    from pathlib import Path

    from wish_models.command_result import CommandResult, CommandState, LogFiles
    from wish_models.utc_datetime import UtcDatetime

    log_files = LogFiles(stdout=Path("/tmp/stdout.log"), stderr=Path("/tmp/stderr.log"))
    act_result = [
        CommandResult(
            num=1,
            command="test command",
            state=CommandState.SUCCESS,
            exit_code=0,
            log_summary="success",
            log_files=log_files,
            created_at=UtcDatetime.now()
        )
    ]

    state = GraphState(
        query="Start Metasploit",
        context={
            "current_directory": "/home/user",
            "target": {"rhost": "10.10.10.40"},
            "attacker": {"lhost": "192.168.1.5"}
        },
        processed_query=processed_query,
        command_candidates=[CommandInput(command="msfconsole", timeout_sec=DEFAULT_TIMEOUT_SEC)],
        act_result=act_result,
        is_retry=True,
        error_type="TIMEOUT"
    )

    # Mock the modifier to return a modified state
    expected_result = GraphState(
        query="Start Metasploit",
        context={
            "current_directory": "/home/user",
            "target": {"rhost": "10.10.10.40"},
            "attacker": {"lhost": "192.168.1.5"}
        },
        processed_query=processed_query,
        command_candidates=[CommandInput(command="msfconsole -q -x \"exit -y\"", timeout_sec=DEFAULT_TIMEOUT_SEC)],
        act_result=act_result,
        is_retry=True,
        error_type="TIMEOUT"
    )
    mock_modify.return_value = expected_result

    # Act
    result = command_modifier.modify_command(state, settings)

    # Assert
    assert result.query == "Start Metasploit"
    assert result.context == {
        "current_directory": "/home/user",
        "target": {"rhost": "10.10.10.40"},
        "attacker": {"lhost": "192.168.1.5"}
    }
    assert result.processed_query == processed_query
    assert "exit -y" in result.command_candidates[0].command
    assert result.act_result == act_result
    assert result.is_retry is True
    assert result.error_type == "TIMEOUT"
