"""Unit tests for the command modifier node."""

import json
from unittest.mock import MagicMock, patch

import pytest
from wish_models.settings import Settings

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


@patch("langchain_openai.ChatOpenAI")
def test_modify_command_dialog_avoidance(mock_chat, settings):
    """Test dialog avoidance modification."""
    # Arrange
    # Mock the LLM and chain
    mock_instance = MagicMock()
    mock_chain = MagicMock()
    mock_instance.__or__.return_value = mock_chain
    mock_chat.return_value = mock_instance

    # Mock the LLM responses for dialog avoidance and list files
    mock_chain.invoke.side_effect = [
        # Dialog avoidance response
        json.dumps({
            "command": "msfconsole -q -x \"use exploit/multi/handler; set PAYLOAD windows/meterpreter/reverse_tcp; "
                       "set LHOST 10.10.10.1; set LPORT 4444; run; exit -y\""
        }),
        # List files response (no change)
        json.dumps({
            "command": "msfconsole -q -x \"use exploit/multi/handler; set PAYLOAD windows/meterpreter/reverse_tcp; "
                       "set LHOST 10.10.10.1; set LPORT 4444; run; exit -y\""
        })
    ]

    # Create a state with an interactive command
    state = GraphState(
        query="Start a Metasploit handler",
        context={},
        command_candidates=["msfconsole"]
    )

    # Act
    result = command_modifier.modify_command(state, settings)

    # Assert
    assert len(result.command_candidates) == 1
    assert "exit -y" in result.command_candidates[0]

    # Verify the LLM was called correctly
    assert mock_chat.call_count == 1
    assert mock_chain.invoke.call_count == 2

    # Check that the dialog avoidance document was used
    args, _ = mock_chain.invoke.call_args_list[0]
    prompt_args = args[0]
    assert "対話回避" in str(prompt_args)


@patch("langchain_openai.ChatOpenAI")
def test_modify_command_list_files(mock_chat, settings):
    """Test list files modification."""
    # Arrange
    # Mock the LLM and chain
    mock_instance = MagicMock()
    mock_chain = MagicMock()
    mock_instance.__or__.return_value = mock_chain
    mock_chat.return_value = mock_instance

    # Mock the LLM responses for dialog avoidance and list files
    mock_chain.invoke.side_effect = [
        # Dialog avoidance response (no change)
        json.dumps({
            "command": "hydra -L user_list.txt -P pass_list.txt smb://10.10.10.40"
        }),
        # List files response
        json.dumps({
            "command": "hydra -L /usr/share/seclists/Usernames/top-usernames-shortlist.txt "
                       "-P /usr/share/seclists/Passwords/xato-net-10-million-passwords-1000.txt smb://10.10.10.40"
        })
    ]

    # Create a state with a command using list files
    state = GraphState(
        query="Brute force SMB login",
        context={},
        command_candidates=["hydra -L user_list.txt -P pass_list.txt smb://10.10.10.40"]
    )

    # Act
    result = command_modifier.modify_command(state, settings)

    # Assert
    assert len(result.command_candidates) == 1
    assert "/usr/share/seclists/Usernames/top-usernames-shortlist.txt" in result.command_candidates[0]
    assert "/usr/share/seclists/Passwords/xato-net-10-million-passwords-1000.txt" in result.command_candidates[0]

    # Verify the LLM was called correctly
    assert mock_chat.call_count == 1
    assert mock_chain.invoke.call_count == 2

    # Check that the list files document was used
    args, _ = mock_chain.invoke.call_args_list[1]
    prompt_args = args[0]
    assert "リストファイル" in str(prompt_args)


@patch("langchain_openai.ChatOpenAI")
def test_modify_command_both_modifications(mock_chat, settings):
    """Test both dialog avoidance and list files modifications."""
    # Arrange
    # Mock the LLM and chain
    mock_instance = MagicMock()
    mock_chain = MagicMock()
    mock_instance.__or__.return_value = mock_chain
    mock_chat.return_value = mock_instance

    # Mock the LLM responses for dialog avoidance and list files
    mock_chain.invoke.side_effect = [
        # Dialog avoidance response
        json.dumps({
            "command": "smbclient -N //10.10.10.40/share -c 'get user_list.txt'"
        }),
        # List files response
        json.dumps({
            "command": "smbclient -N //10.10.10.40/share -c "
                       "'get /usr/share/seclists/Usernames/top-usernames-shortlist.txt'"
        })
    ]

    # Create a state with a command needing both modifications
    state = GraphState(
        query="Download user list from SMB share",
        context={},
        command_candidates=["smbclient -N //10.10.10.40/share"]
    )

    # Act
    result = command_modifier.modify_command(state, settings)

    # Assert
    assert len(result.command_candidates) == 1
    assert "-c 'get" in result.command_candidates[0]
    assert "/usr/share/seclists/Usernames/top-usernames-shortlist.txt" in result.command_candidates[0]


@patch("langchain_openai.ChatOpenAI")
def test_modify_command_json_error(mock_chat, settings):
    """Test handling JSON parsing errors."""
    # Arrange
    # Mock the LLM and chain
    mock_instance = MagicMock()
    mock_chain = MagicMock()
    mock_instance.__or__.return_value = mock_chain
    mock_chat.return_value = mock_instance

    # Mock the LLM response with invalid JSON
    mock_chain.invoke.return_value = "Invalid JSON"

    # Create a state with a command
    state = GraphState(
        query="Start a Metasploit handler",
        context={},
        command_candidates=["msfconsole"]
    )

    # Act
    with patch("wish_command_generation_api.nodes.command_modifier.logger") as mock_logger:
        result = command_modifier.modify_command(state, settings)

        # Assert
        assert result.command_candidates == ["msfconsole"]  # Original command should be preserved
        mock_logger.warning.assert_called()


@patch("langchain_openai.ChatOpenAI")
def test_modify_command_exception(mock_chat, settings):
    """Test handling exceptions during command modification."""
    # Arrange
    # Mock the LLM to raise an exception
    mock_chat.side_effect = Exception("Test error")

    # Create a state with a command
    state = GraphState(
        query="Start a Metasploit handler",
        context={},
        command_candidates=["msfconsole"]
    )

    # Act
    with patch("wish_command_generation_api.nodes.command_modifier.logger") as mock_logger:
        result = command_modifier.modify_command(state, settings)

        # Assert
        assert result.command_candidates == ["msfconsole"]  # Original command should be preserved
        mock_logger.exception.assert_called_once()


@patch("langchain_openai.ChatOpenAI")
def test_modify_command_multiple_commands(mock_chat, settings):
    """Test modifying multiple commands."""
    # Arrange
    # Mock the LLM and chain
    mock_instance = MagicMock()
    mock_chain = MagicMock()
    mock_instance.__or__.return_value = mock_chain
    mock_chat.return_value = mock_instance

    # Mock the LLM responses for dialog avoidance and list files
    # For first command
    mock_chain.invoke.side_effect = [
        # Dialog avoidance for command 1
        json.dumps({
            "command": "msfconsole -q -x \"use exploit/multi/handler; exit -y\""
        }),
        # List files for command 1
        json.dumps({
            "command": "msfconsole -q -x \"use exploit/multi/handler; exit -y\""
        }),
        # Dialog avoidance for command 2
        json.dumps({
            "command": "hydra -L /usr/share/seclists/Usernames/top-usernames-shortlist.txt -P pass_list.txt smb://10.10.10.40"
        }),
        # List files for command 2
        json.dumps({
            "command": "hydra -L /usr/share/seclists/Usernames/top-usernames-shortlist.txt "
                       "-P /usr/share/seclists/Passwords/xato-net-10-million-passwords-1000.txt smb://10.10.10.40"
        })
    ]

    # Create a state with multiple commands
    state = GraphState(
        query="Run multiple commands",
        context={},
        command_candidates=[
            "msfconsole",
            "hydra -L user_list.txt -P pass_list.txt smb://10.10.10.40"
        ]
    )

    # Act
    result = command_modifier.modify_command(state, settings)

    # Assert
    assert len(result.command_candidates) == 2
    assert "exit -y" in result.command_candidates[0]
    assert "/usr/share/seclists/Usernames/top-usernames-shortlist.txt" in result.command_candidates[1]
    assert "/usr/share/seclists/Passwords/xato-net-10-million-passwords-1000.txt" in result.command_candidates[1]

    # Verify the LLM was called correctly
    assert mock_chat.call_count == 1
    assert mock_chain.invoke.call_count == 4


@patch("langchain_openai.ChatOpenAI")
def test_modify_command_preserve_state(mock_chat, settings):
    """Test that the command modifier preserves other state fields."""
    # Arrange
    # Mock the LLM and chain
    mock_instance = MagicMock()
    mock_chain = MagicMock()
    mock_instance.__or__.return_value = mock_chain
    mock_chat.return_value = mock_instance

    # Mock the LLM responses
    mock_chain.invoke.side_effect = [
        # Dialog avoidance response
        json.dumps({
            "command": "msfconsole -q -x \"exit -y\""
        }),
        # List files response
        json.dumps({
            "command": "msfconsole -q -x \"exit -y\""
        })
    ]

    # Create a state with additional fields
    processed_query = "processed test query"
    act_result = [{"command": "test command", "exit_class": "SUCCESS", "exit_code": "0", "log_summary": "success"}]

    state = GraphState(
        query="Start Metasploit",
        context={"current_directory": "/home/user"},
        processed_query=processed_query,
        command_candidates=["msfconsole"],
        act_result=act_result,
        is_retry=True,
        error_type="TIMEOUT"
    )

    # Act
    result = command_modifier.modify_command(state, settings)

    # Assert
    assert result.query == "Start Metasploit"
    assert result.context == {"current_directory": "/home/user"}
    assert result.processed_query == processed_query
    assert "exit -y" in result.command_candidates[0]
    assert result.act_result == act_result
    assert result.is_retry is True
    assert result.error_type == "TIMEOUT"
