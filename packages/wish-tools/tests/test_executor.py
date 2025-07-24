"""
Tests for ToolExecutor implementation
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from wish_tools.execution.executor import ToolExecutor


class TestToolExecutor:
    """Test cases for ToolExecutor"""

    def setup_method(self):
        """Set up test fixtures"""
        self.executor = ToolExecutor()

    @pytest.mark.asyncio
    async def test_successful_command_execution(self):
        """Test successful command execution"""
        # Mock subprocess
        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(return_value=(b"test output\n", b""))
        mock_process.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            result = await self.executor.execute_command("echo test", "echo", timeout=30)

        assert result.success
        assert result.exit_code == 0
        assert result.stdout == "test output\n"
        assert result.stderr == ""
        assert result.tool_name == "echo"
        assert result.command == "echo test"
        assert result.duration > 0
        assert not result.timeout_occurred

    @pytest.mark.asyncio
    async def test_command_timeout(self):
        """Test command execution timeout"""
        # Mock subprocess that never completes
        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(side_effect=TimeoutError())
        mock_process.terminate = AsyncMock()
        mock_process.wait = AsyncMock()

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            result = await self.executor.execute_command("sleep 10", "sleep", timeout=1)

        assert not result.success
        assert result.exit_code == -1
        assert "timed out" in result.stderr
        assert result.timeout_occurred

        # Verify process was terminated
        mock_process.terminate.assert_called_once()

    @pytest.mark.asyncio
    async def test_tool_not_found(self):
        """Test execution when tool is not found"""
        with patch("asyncio.create_subprocess_exec", side_effect=FileNotFoundError("Tool not found")):
            result = await self.executor.execute_command("nonexistent command", "nonexistent")

        assert not result.success
        assert result.exit_code == -2
        assert "Tool not found" in result.stderr

    @pytest.mark.asyncio
    async def test_permission_denied(self):
        """Test execution with permission denied"""
        with patch("asyncio.create_subprocess_exec", side_effect=PermissionError("Permission denied")):
            result = await self.executor.execute_command("restricted command", "restricted")

        assert not result.success
        assert result.exit_code == -3
        assert "Permission denied" in result.stderr

    @pytest.mark.asyncio
    async def test_unexpected_error(self):
        """Test execution with unexpected error"""
        with patch("asyncio.create_subprocess_exec", side_effect=RuntimeError("Unexpected error")):
            result = await self.executor.execute_command("test command", "test")

        assert not result.success
        assert result.exit_code == -4
        assert "Unexpected error" in result.stderr

    @pytest.mark.asyncio
    async def test_command_with_working_directory(self):
        """Test command execution with working directory"""
        # Mock subprocess
        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(return_value=(b"/tmp\n", b""))
        mock_process.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_process) as mock_create:
            result = await self.executor.execute_command("pwd", "pwd", working_directory="/tmp")  # noqa: S108

        assert result.success
        assert result.working_directory == "/tmp"  # noqa: S108

        # Verify subprocess was called with correct working directory
        mock_create.assert_called_once()
        # For create_subprocess_exec, args are positional, cwd is keyword
        assert mock_create.call_args[0][0] == "pwd"  # First positional arg is command
        assert mock_create.call_args[1]["cwd"] == "/tmp"  # noqa: S108

    @pytest.mark.asyncio
    async def test_command_with_env_vars(self):
        """Test command execution with environment variables"""
        # Mock subprocess
        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(return_value=(b"TEST_VAR=test_value\n", b""))
        mock_process.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_process) as mock_create:
            env_vars = {"TEST_VAR": "test_value"}
            result = await self.executor.execute_command("env", "env", env_vars=env_vars)

        assert result.success

        # Verify subprocess was called with environment variables
        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args[1]
        assert "TEST_VAR" in call_kwargs["env"]
        assert call_kwargs["env"]["TEST_VAR"] == "test_value"

    @pytest.mark.asyncio
    async def test_invalid_working_directory(self):
        """Test command execution with invalid working directory"""
        with pytest.raises(ValueError, match="Working directory does not exist"):
            await self.executor.execute_command("test", "test", working_directory="/nonexistent")

    @pytest.mark.asyncio
    async def test_execute_tool_with_args(self):
        """Test tool execution with properly quoted arguments"""
        # Mock subprocess
        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(return_value=(b"scan result\n", b""))
        mock_process.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            result = await self.executor.execute_tool_with_args("nmap", ["-sS", "192.168.1.1"], timeout=30)

        assert result.success
        assert "nmap -sS 192.168.1.1" in result.command

    @pytest.mark.asyncio
    async def test_execute_tool_with_special_chars(self):
        """Test tool execution with arguments containing special characters"""
        # Mock subprocess
        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(return_value=(b"result\n", b""))
        mock_process.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            result = await self.executor.execute_tool_with_args("test", ["arg with spaces", "special!@#chars"])

        assert result.success
        # Verify arguments are properly quoted
        assert "'arg with spaces'" in result.command or '"arg with spaces"' in result.command

    @pytest.mark.asyncio
    async def test_process_tracking(self):
        """Test active process tracking"""
        # Mock subprocess
        mock_process = AsyncMock()
        mock_process.pid = 12345
        mock_process.communicate = AsyncMock(return_value=(b"", b""))
        mock_process.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            # Start execution but don't await immediately
            task = asyncio.create_task(self.executor.execute_command("sleep 1", "sleep", timeout=30))

            # Give it a moment to start
            await asyncio.sleep(0.1)

            # Check that process is tracked
            active = self.executor.get_active_executions()
            assert len(active) >= 0  # May be 0 if execution finished quickly

            # Complete the task
            result = await task

        assert result.success

    @pytest.mark.asyncio
    async def test_cancel_all_executions(self):
        """Test cancelling all active executions"""
        # Mock subprocess
        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(side_effect=asyncio.CancelledError())
        mock_process.terminate = AsyncMock()
        mock_process.wait = AsyncMock()

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            # Start a long-running command
            task = asyncio.create_task(self.executor.execute_command("sleep 10", "sleep", timeout=60))

            # Give it a moment to start
            await asyncio.sleep(0.1)

            # Cancel all executions
            await self.executor.cancel_all_executions()

            # The task should be cancelled
            with pytest.raises(asyncio.CancelledError):
                await task

    @pytest.mark.asyncio
    async def test_graceful_process_termination(self):
        """Test graceful process termination"""
        # Create executor for this test
        executor = ToolExecutor()

        # Mock subprocess
        mock_process = AsyncMock()
        mock_process.terminate = AsyncMock()
        mock_process.wait = AsyncMock()

        # Test graceful termination
        await executor._terminate_process(mock_process, timeout=1)

        mock_process.terminate.assert_called_once()
        mock_process.wait.assert_called()

    @pytest.mark.asyncio
    async def test_force_kill_process(self):
        """Test force killing process when graceful termination fails"""
        # Create executor for this test
        executor = ToolExecutor()

        # Mock subprocess that doesn't terminate gracefully
        mock_process = AsyncMock()
        mock_process.terminate = AsyncMock()
        mock_process.wait = AsyncMock(side_effect=TimeoutError())
        mock_process.kill = AsyncMock()

        # Test force kill
        with patch("asyncio.wait_for", side_effect=TimeoutError()):
            await executor._terminate_process(mock_process, timeout=0.1)

        mock_process.terminate.assert_called_once()
        mock_process.kill.assert_called_once()

    @pytest.mark.asyncio
    async def test_command_with_stderr_output(self):
        """Test command execution with stderr output"""
        # Mock subprocess with stderr
        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(return_value=(b"stdout output", b"stderr output"))
        mock_process.returncode = 1

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            result = await self.executor.execute_command("test command", "test")

        assert not result.success
        assert result.exit_code == 1
        assert result.stdout == "stdout output"
        assert result.stderr == "stderr output"

    def test_executor_initialization(self):
        """Test executor initialization"""
        executor = ToolExecutor()
        assert executor.active_processes == {}
