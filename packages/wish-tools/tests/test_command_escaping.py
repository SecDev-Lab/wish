"""Tests for command escaping in tool execution."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from wish_tools.execution.executor import ToolExecutor


class TestCommandEscaping:
    """Test command escaping to prevent shell injection and syntax errors."""

    @pytest.fixture
    def tool_executor(self):
        """Create ToolExecutor instance."""
        return ToolExecutor()

    @pytest.mark.asyncio
    async def test_searchsploit_command_with_special_chars(self, tool_executor):
        """Test searchsploit commands with special characters."""
        test_cases = [
            # Basic CVE search
            ("searchsploit CVE-2007-2447", ["searchsploit", "CVE-2007-2447"]),
            # Search with quotes
            ("searchsploit samba 'username map'", ["searchsploit", "samba", "username map"]),
            # Search with double quotes
            ('searchsploit "samba 3.0"', ["searchsploit", "samba 3.0"]),
            # Search with potential shell expansion - should be treated as literal
            ("searchsploit samba '$(whoami)'", ["searchsploit", "samba", "$(whoami)"]),
            # Search with semicolon - should fail to parse
            ("searchsploit samba; ls", None),  # Will fail shlex parsing
            # Search with pipe - should fail to parse
            ("searchsploit samba | grep RCE", None),  # Will fail shlex parsing
        ]

        for input_cmd, expected_args in test_cases:
            # Mock asyncio.create_subprocess_exec to capture the actual command
            with patch("asyncio.create_subprocess_exec") as mock_exec:
                mock_process = Mock()
                mock_process.communicate = AsyncMock(return_value=(b"Search results...", b""))
                mock_process.returncode = 0
                mock_exec.return_value = mock_process

                # Execute command
                result = await tool_executor.execute_command(command=input_cmd, tool_name="searchsploit", timeout=30)

                if expected_args is None:
                    # Should fail due to shell metacharacters
                    assert not result.success
                    assert "shell metacharacter" in result.stderr or "Failed to parse" in result.stderr
                    mock_exec.assert_not_called()
                else:
                    # Verify command was executed safely
                    assert result.success
                    mock_exec.assert_called_once()
                    # Check that the command was split correctly
                    actual_args = list(mock_exec.call_args[0])
                    assert actual_args == expected_args

    @pytest.mark.asyncio
    async def test_nmap_command_escaping(self, tool_executor):
        """Test nmap commands with special characters in arguments."""
        test_cases = [
            # IP with potential injection - should fail to parse
            ("nmap 10.10.10.3; cat /etc/passwd", None),
            # Script argument with quotes
            ('nmap --script="smb-vuln-*" 10.10.10.3', ["nmap", "--script=smb-vuln-*", "10.10.10.3"]),
            # Script argument without quotes
            ("nmap --script=smb-vuln-* 10.10.10.3", ["nmap", "--script=smb-vuln-*", "10.10.10.3"]),
            # Output file with spaces
            ("nmap -oN 'scan results.txt' 10.10.10.3", ["nmap", "-oN", "scan results.txt", "10.10.10.3"]),
        ]

        for input_cmd, expected_args in test_cases:
            with patch("asyncio.create_subprocess_exec") as mock_exec:
                mock_process = Mock()
                mock_process.communicate = AsyncMock(return_value=(b"Nmap scan report...", b""))
                mock_process.returncode = 0
                mock_exec.return_value = mock_process

                result = await tool_executor.execute_command(command=input_cmd, tool_name="nmap", timeout=30)

                if expected_args is None:
                    # Should fail due to shell metacharacter
                    assert not result.success
                    assert "shell metacharacter" in result.stderr
                    mock_exec.assert_not_called()
                else:
                    assert result.success
                    mock_exec.assert_called_once()
                    actual_args = list(mock_exec.call_args[0])
                    assert actual_args == expected_args

    @pytest.mark.asyncio
    async def test_smbclient_command_escaping(self, tool_executor):
        """Test smbclient commands with special characters."""
        test_cases = [
            # Password with special chars
            (
                "smbclient //10.10.10.3/share -U user%pass@word",
                ["smbclient", "//10.10.10.3/share", "-U", "user%pass@word"],
            ),
            # Command with quotes
            ("smbclient //10.10.10.3/share -c 'ls'", ["smbclient", "//10.10.10.3/share", "-c", "ls"]),
            # Multiple commands - semicolon inside quotes is OK
            (
                'smbclient //10.10.10.3/share -c "ls; get file.txt"',
                ["smbclient", "//10.10.10.3/share", "-c", "ls; get file.txt"],
            ),
        ]

        for input_cmd, expected_args in test_cases:
            with patch("asyncio.create_subprocess_exec") as mock_exec:
                mock_process = Mock()
                mock_process.communicate = AsyncMock(return_value=(b"Domain=[WORKGROUP]...", b""))
                mock_process.returncode = 0
                mock_exec.return_value = mock_process

                result = await tool_executor.execute_command(command=input_cmd, tool_name="smbclient", timeout=30)

                assert result.success
                mock_exec.assert_called_once()
                actual_args = list(mock_exec.call_args[0])
                assert actual_args == expected_args

    @pytest.mark.asyncio
    async def test_command_with_newlines(self, tool_executor):
        """Test commands containing newline characters."""
        # Command with newline (potential for injection)
        dangerous_cmd = "nmap 10.10.10.3\ncat /etc/passwd"

        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_process = Mock()
            mock_process.communicate = AsyncMock(return_value=(b"Nmap scan report...", b""))
            mock_process.returncode = 0
            mock_exec.return_value = mock_process

            # This should parse but newline will be part of arguments
            result = await tool_executor.execute_command(command=dangerous_cmd, tool_name="nmap", timeout=30)

            # With shlex, newline doesn't cause parse error, it just splits into multiple args
            assert result.success
            mock_exec.assert_called_once()
            actual_args = list(mock_exec.call_args[0])
            # The command is split into ["nmap", "10.10.10.3", "cat", "/etc/passwd"]
            # This is safe because "cat" and "/etc/passwd" are just arguments to nmap
            assert len(actual_args) == 4
            assert actual_args[0] == "nmap"
            assert actual_args[1] == "10.10.10.3"
            assert actual_args[2] == "cat"
            assert actual_args[3] == "/etc/passwd"

    @pytest.mark.asyncio
    async def test_empty_command(self, tool_executor):
        """Test handling of empty commands."""
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            result = await tool_executor.execute_command(command="", tool_name="nmap", timeout=30)

            # Should handle empty command gracefully
            assert not result.success
            assert "Empty command provided" in result.stderr
            assert result.exit_code == -5
            mock_exec.assert_not_called()

    @pytest.mark.asyncio
    async def test_command_with_null_bytes(self, tool_executor):
        """Test commands containing null bytes."""
        dangerous_cmd = "nmap 10.10.10.3\x00cat /etc/passwd"

        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_process = Mock()
            mock_process.communicate = AsyncMock(return_value=(b"Nmap scan report...", b""))
            mock_process.returncode = 0
            mock_exec.return_value = mock_process

            result = await tool_executor.execute_command(command=dangerous_cmd, tool_name="nmap", timeout=30)

            # With exec, null bytes in arguments are passed as-is (but won't execute as separate command)
            # The command should succeed but the null byte is part of the argument
            assert result.success
            mock_exec.assert_called_once()
            actual_args = list(mock_exec.call_args[0])
            # The null byte should be in the IP address argument
            assert "10.10.10.3\x00cat" in actual_args[1]

    @pytest.mark.asyncio
    async def test_complex_shell_commands(self, tool_executor):
        """Test that complex shell commands requiring pipes/redirects fail appropriately."""
        test_cases = [
            # Pipe command
            "nmap -sV 10.10.10.3 | grep open",
            # Output redirection
            "nmap -sV 10.10.10.3 > scan.txt",
            # Input redirection
            "hydra -L users.txt < passwords.txt",
            # Background execution
            "nmap -sV 10.10.10.3 &",
            # Command chaining with &&
            "nmap -sV 10.10.10.3 && echo done",
            # Command chaining with ||
            "nmap -sV 10.10.10.3 || echo failed",
        ]

        for cmd in test_cases:
            with patch("asyncio.create_subprocess_exec") as mock_exec:
                result = await tool_executor.execute_command(command=cmd, tool_name="nmap", timeout=30)

                # These should all fail due to shell metacharacters
                assert not result.success
                assert "shell metacharacter" in result.stderr
                mock_exec.assert_not_called()
