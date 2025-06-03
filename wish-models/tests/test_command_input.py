"""Tests for CommandInput model with tool_type and tool_parameters."""

import pytest
from wish_models.command_result import CommandInput, CommandType


def test_command_input_basic():
    """Test basic CommandInput creation."""
    cmd = CommandInput(
        command="ls -la",
        timeout_sec=60
    )
    assert cmd.command == "ls -la"
    assert cmd.timeout_sec == 60
    assert cmd.tool_type is None
    assert cmd.tool_parameters is None


def test_command_input_with_tool_type():
    """Test CommandInput with tool_type."""
    cmd = CommandInput(
        command="exploit",
        timeout_sec=300,
        tool_type=CommandType.MSFCONSOLE
    )
    assert cmd.command == "exploit"
    assert cmd.timeout_sec == 300
    assert cmd.tool_type == CommandType.MSFCONSOLE
    assert cmd.tool_parameters is None


def test_command_input_with_tool_parameters():
    """Test CommandInput with tool_type and parameters."""
    params = {
        "module": "exploit/windows/smb/ms17_010_eternalblue",
        "rhosts": "10.10.10.40",
        "lhost": "10.10.14.12"
    }
    cmd = CommandInput(
        command="exploit",
        timeout_sec=600,
        tool_type=CommandType.MSFCONSOLE,
        tool_parameters=params
    )
    assert cmd.command == "exploit"
    assert cmd.timeout_sec == 600
    assert cmd.tool_type == CommandType.MSFCONSOLE
    assert cmd.tool_parameters == params
    assert cmd.tool_parameters["module"] == "exploit/windows/smb/ms17_010_eternalblue"


def test_command_input_serialization():
    """Test CommandInput serialization/deserialization."""
    params = {"key": "value"}
    cmd = CommandInput(
        command="test",
        timeout_sec=30,
        tool_type=CommandType.BASH,
        tool_parameters=params
    )
    
    # Serialize to dict
    data = cmd.model_dump()
    assert data["command"] == "test"
    assert data["timeout_sec"] == 30
    assert data["tool_type"] == CommandType.BASH
    assert data["tool_parameters"] == params
    
    # Deserialize from dict
    cmd2 = CommandInput.model_validate(data)
    assert cmd2.command == cmd.command
    assert cmd2.timeout_sec == cmd.timeout_sec
    assert cmd2.tool_type == cmd.tool_type
    assert cmd2.tool_parameters == cmd.tool_parameters