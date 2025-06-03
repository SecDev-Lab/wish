"""Tests for msfconsole command execution."""

import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from pathlib import Path

from wish_models import Wish, WishState, CommandResult
from wish_models.command_result import CommandInput, CommandType
from wish_models.utc_datetime import UtcDatetime
from wish_command_execution.command_executor import CommandExecutor


@pytest.mark.asyncio
async def test_execute_msfconsole_command():
    """Test executing a command with msfconsole tool type."""
    # Create wish
    wish = Wish(
        id="test123",
        wish="Test msfconsole",
        state=WishState.DOING,
        command_results=[],
        created_at=UtcDatetime.now()
    )
    
    # Create command input with msfconsole type
    cmd_input = CommandInput(
        command="search cve:2017-0144",
        timeout_sec=30,
        tool_type=CommandType.MSFCONSOLE,
        tool_parameters={}
    )
    
    # Mock MsfconsoleTool
    with patch('wish_command_execution.command_executor.MsfconsoleTool') as mock_tool_class:
        # Create mock tool instance
        mock_tool = AsyncMock()
        mock_tool_class.return_value = mock_tool
        
        # Mock tool result
        mock_result = Mock()
        mock_result.success = True
        mock_result.output = "Found modules for CVE-2017-0144..."
        mock_result.error = ""
        mock_result.exit_code = 0
        mock_tool.execute.return_value = mock_result
        
        # Create executor
        executor = CommandExecutor()
        
        # Execute command
        await executor.execute_commands(wish, [cmd_input])
        
        # Verify MsfconsoleTool was used
        mock_tool_class.assert_called_once()
        mock_tool.execute.assert_called_once()
        
        # Check command result
        assert len(wish.command_results) == 1
        result = wish.command_results[0]
        assert result.command == "search cve:2017-0144"
        assert result.timeout_sec == 30


@pytest.mark.asyncio
async def test_execute_bash_command():
    """Test that bash commands still work normally."""
    # Create wish
    wish = Wish(
        id="test456",
        wish="Test bash",
        state=WishState.DOING,
        command_results=[],
        created_at=UtcDatetime.now()
    )
    
    # Create command input without tool_type (defaults to bash)
    cmd_input = CommandInput(
        command="echo 'Hello World'",
        timeout_sec=10
    )
    
    # Mock bash backend
    mock_backend = AsyncMock()
    executor = CommandExecutor(backend=mock_backend)
    
    # Execute command
    await executor.execute_commands(wish, [cmd_input])
    
    # Verify bash backend was used
    mock_backend.execute_command.assert_called_once()
    call_args = mock_backend.execute_command.call_args
    assert call_args[0][1] == "echo 'Hello World'"  # command
    assert call_args[0][4] == 10  # timeout_sec


@pytest.mark.asyncio
async def test_msfconsole_exploit_command():
    """Test executing an exploit command with msfconsole."""
    wish = Wish(
        id="test789",
        wish="Test exploit",
        state=WishState.DOING,
        command_results=[],
        created_at=UtcDatetime.now()
    )
    
    cmd_input = CommandInput(
        command="exploit",
        timeout_sec=600,
        tool_type=CommandType.MSFCONSOLE,
        tool_parameters={
            "module": "exploit/windows/smb/ms17_010_eternalblue",
            "rhosts": "10.10.10.40",
            "lhost": "10.10.14.12"
        }
    )
    
    with patch('wish_command_execution.command_executor.MsfconsoleTool') as mock_tool_class:
        mock_tool = AsyncMock()
        mock_tool_class.return_value = mock_tool
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.output = "[*] Started exploit..."
        mock_result.error = ""
        mock_result.exit_code = 0
        mock_tool.execute.return_value = mock_result
        
        executor = CommandExecutor()
        await executor.execute_commands(wish, [cmd_input])
        
        # Verify tool was called with correct parameters
        tool_command = mock_tool.execute.call_args[0][0]
        assert tool_command.command == "exploit"
        assert tool_command.timeout_sec == 600
        assert tool_command.tool_parameters["module"] == "exploit/windows/smb/ms17_010_eternalblue"