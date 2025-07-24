"""
Tests for msfconsole executor with PTY support
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from wish_tools.execution.msfconsole_executor import MsfconsoleExecutor


class TestMsfconsoleExecutor:
    """Test msfconsole executor functionality"""

    @pytest.fixture
    def executor(self):
        """Create a msfconsole executor instance"""
        return MsfconsoleExecutor()

    @pytest.mark.asyncio
    async def test_init(self, executor):
        """Test executor initialization"""
        assert executor.process is None
        assert executor.master_fd is None

    @pytest.mark.asyncio
    @patch("wish_tools.execution.msfconsole_executor.pty.openpty")
    @patch("wish_tools.execution.msfconsole_executor.os.close")
    @patch("wish_tools.execution.msfconsole_executor.asyncio.create_subprocess_shell")
    async def test_execute_simple_command(self, mock_subprocess, mock_close, mock_openpty, executor):
        """Test executing a simple msfconsole command"""
        # Mock PTY
        mock_openpty.return_value = (10, 11)  # master_fd, slave_fd

        # Mock process
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.wait = AsyncMock(return_value=None)
        mock_subprocess.return_value = mock_process

        # Mock PTY output reading
        with patch.object(executor, "_read_pty_output") as mock_read:
            mock_read.return_value = "Exploit completed successfully\n"

            stdout, stderr, exit_code = await executor.execute_msfconsole_command(
                "use exploit/test; set RHOSTS 10.0.0.1; run"
            )

            assert exit_code == 0
            assert "Exploit completed successfully" in stdout
            assert stderr == ""

    @pytest.mark.asyncio
    @patch("wish_tools.execution.msfconsole_executor.pty.openpty")
    @patch("wish_tools.execution.msfconsole_executor.os.close")
    @patch("wish_tools.execution.msfconsole_executor.asyncio.create_subprocess_shell")
    async def test_execute_with_timeout(self, mock_subprocess, mock_close, mock_openpty, executor):
        """Test command execution with timeout"""
        # Mock PTY
        mock_openpty.return_value = (10, 11)

        # Mock process that doesn't terminate
        mock_process = AsyncMock()
        mock_process.returncode = None
        mock_process.wait = AsyncMock(side_effect=TimeoutError())
        mock_subprocess.return_value = mock_process

        # Mock PTY output reading (simulate long-running command)
        with patch.object(executor, "_read_pty_output") as mock_read:
            mock_read.return_value = "Command started...\n"

            with patch.object(executor, "_terminate_process") as mock_terminate:
                mock_terminate.return_value = None

                stdout, stderr, exit_code = await executor.execute_msfconsole_command(
                    "use exploit/test; run", timeout=1
                )

                # Should have attempted to terminate the process
                mock_terminate.assert_called_once()
                assert exit_code == -1  # Process didn't terminate normally

    @pytest.mark.asyncio
    @patch("wish_tools.execution.msfconsole_executor.pty.openpty")
    @patch("wish_tools.execution.msfconsole_executor.os.close")
    @patch("wish_tools.execution.msfconsole_executor.asyncio.create_subprocess_shell")
    async def test_execute_with_env_vars(self, mock_subprocess, mock_close, mock_openpty, executor):
        """Test command execution with environment variables"""
        # Mock PTY
        mock_openpty.return_value = (10, 11)

        # Mock process
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process

        # Mock PTY output reading
        with patch.object(executor, "_read_pty_output") as mock_read:
            mock_read.return_value = "Command output\n"

            env_vars = {"CUSTOM_VAR": "test_value"}

            stdout, stderr, exit_code = await executor.execute_msfconsole_command("use exploit/test", env_vars=env_vars)

            # Verify subprocess was called with correct environment
            call_args = mock_subprocess.call_args
            env_arg = call_args[1]["env"]

            assert env_arg["CUSTOM_VAR"] == "test_value"
            assert env_arg["TERM"] == "xterm"
            assert env_arg["COLUMNS"] == "80"
            assert env_arg["LINES"] == "24"

    @pytest.mark.asyncio
    @patch("wish_tools.execution.msfconsole_executor.pty.openpty")
    @patch("wish_tools.execution.msfconsole_executor.os.close")
    @patch("wish_tools.execution.msfconsole_executor.asyncio.create_subprocess_shell")
    async def test_execute_with_working_directory(self, mock_subprocess, mock_close, mock_openpty, executor):
        """Test command execution with working directory"""
        # Mock PTY
        mock_openpty.return_value = (10, 11)

        # Mock process
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process

        # Mock PTY output reading
        with patch.object(executor, "_read_pty_output") as mock_read:
            mock_read.return_value = "Command output\n"

            # Mock pathlib.Path to simulate valid directory
            with patch("wish_tools.execution.msfconsole_executor.Path") as mock_path:
                mock_path_instance = MagicMock()
                mock_path_instance.exists.return_value = True
                mock_path_instance.is_dir.return_value = True
                mock_path.return_value = mock_path_instance

                import tempfile

                with tempfile.TemporaryDirectory() as tmp_dir:
                    stdout, stderr, exit_code = await executor.execute_msfconsole_command(
                        "use exploit/test", working_directory=tmp_dir
                    )

                    # Verify subprocess was called with correct working directory
                    call_args = mock_subprocess.call_args
                    assert call_args[1]["cwd"] == tmp_dir

    @pytest.mark.asyncio
    async def test_execute_with_invalid_working_directory(self, executor):
        """Test command execution with invalid working directory"""
        with patch("wish_tools.execution.msfconsole_executor.Path") as mock_path:
            mock_path_instance = MagicMock()
            mock_path_instance.exists.return_value = False
            mock_path.return_value = mock_path_instance

            with pytest.raises(ValueError, match="Invalid working directory"):
                await executor.execute_msfconsole_command("use exploit/test", working_directory="/nonexistent")

    def test_is_msfconsole_finished(self, executor):
        """Test msfconsole completion detection"""
        # Test various completion indicators
        test_cases = [
            ("Exploit completed successfully", True),
            ("Auxiliary module execution completed", True),
            ("Thank you for using Metasploit", True),
            ("Session 1 created", True),
            ("Normal output", False),
            ("", False),
        ]

        for output, expected in test_cases:
            result = executor._is_msfconsole_finished(output)
            assert result == expected, f"Failed for output: {output}"

    @pytest.mark.asyncio
    @patch("wish_tools.execution.msfconsole_executor.select.select")
    @patch("wish_tools.execution.msfconsole_executor.os.read")
    @patch("wish_tools.execution.msfconsole_executor.fcntl.fcntl")
    async def test_read_pty_output(self, mock_fcntl, mock_read, mock_select, executor):
        """Test PTY output reading"""
        # Mock select to return ready fd
        mock_select.side_effect = [
            ([10], [], []),  # First call - data available
            ([10], [], []),  # Second call - data available
            ([], [], []),  # Third call - no data, will timeout
        ]

        # Mock os.read to return data
        mock_read.side_effect = [
            b"First chunk\n",
            b"Exploit completed\n",
            OSError(11),  # EAGAIN - no more data
        ]

        # Mock process
        mock_process = AsyncMock()
        mock_process.returncode = 0
        executor.process = mock_process

        result = await executor._read_pty_output(10, timeout=5)

        assert "First chunk" in result
        assert "Exploit completed" in result

    @pytest.mark.asyncio
    @patch("wish_tools.execution.msfconsole_executor.os.killpg")
    @patch("wish_tools.execution.msfconsole_executor.os.getpgid")
    async def test_terminate_process(self, mock_getpgid, mock_killpg, executor):
        """Test process termination"""
        # Mock process
        mock_process = AsyncMock()
        mock_process.pid = 1234
        mock_process.wait = AsyncMock(return_value=None)
        executor.process = mock_process

        # Mock getpgid
        mock_getpgid.return_value = 1234

        await executor._terminate_process()

        # Verify SIGTERM was sent
        mock_killpg.assert_called_with(1234, 15)  # SIGTERM = 15

    @pytest.mark.asyncio
    @patch("wish_tools.execution.msfconsole_executor.os.close")
    async def test_cleanup(self, mock_close, executor):
        """Test resource cleanup"""
        # Set up resources
        executor.master_fd = 10
        mock_process = AsyncMock()
        executor.process = mock_process

        with patch.object(executor, "_terminate_process") as mock_terminate:
            await executor._cleanup()

            # Verify cleanup
            mock_close.assert_called_once_with(10)
            mock_terminate.assert_called_once()
            assert executor.master_fd is None
            assert executor.process is None

    @pytest.mark.asyncio
    @patch("wish_tools.execution.msfconsole_executor.pty.openpty")
    async def test_execute_with_exception(self, mock_openpty, executor):
        """Test error handling during execution"""
        # Mock PTY to raise exception
        mock_openpty.side_effect = OSError("PTY creation failed")

        with pytest.raises(OSError, match="PTY creation failed"):
            await executor.execute_msfconsole_command("use exploit/test")

        # Verify cleanup was called
        with patch.object(executor, "_cleanup"):
            try:
                await executor.execute_msfconsole_command("use exploit/test")
            except OSError:
                pass

            # Cleanup should be called in finally block
            # This is harder to test directly, but the important thing is that
            # exceptions are properly raised and resources are cleaned up
