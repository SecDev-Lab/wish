import json
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

from wish_models import CommandResult, CommandState, LogFiles, WishState
from wish_models.test_factories import LogFilesFactory, WishDoingFactory, WishDoneFactory
from wish_models.test_factories.command_result_factory import CommandResultDoingFactory

from wish_sh.settings import Settings
from wish_sh.wish_manager import WishManager
from wish_sh.wish_paths import WishPaths


class TestWishManager:
    def test_initialization(self):
        """Test that WishManager initializes with the correct attributes."""
        settings = Settings()

        with patch.object(WishPaths, "ensure_directories") as mock_ensure_dirs:
            manager = WishManager(settings)

            assert manager.settings == settings
            assert isinstance(manager.paths, WishPaths)
            assert manager.current_wish is None
            assert manager.running_commands == {}
            mock_ensure_dirs.assert_called_once()

    @patch("builtins.open", new_callable=mock_open)
    def test_save_wish(self, mock_file):
        """Test that save_wish writes the wish to the history file."""
        settings = Settings()
        manager = WishManager(settings)
        wish = WishDoneFactory.create()

        manager.save_wish(wish)

        mock_file.assert_called_with(manager.paths.history_path, "a")
        mock_file().write.assert_called_once()
        # Check that the written string is valid JSON and contains the wish data
        written_data = mock_file().write.call_args[0][0].strip()
        wish_dict = json.loads(written_data)
        assert wish_dict["id"] == wish.id
        assert wish_dict["wish"] == wish.wish

    @patch("builtins.open", new_callable=mock_open)
    def test_load_wishes_empty_file(self, mock_file):
        """Test that load_wishes returns an empty list when the history file is empty."""
        mock_file.return_value.__enter__.return_value.readlines.return_value = []

        settings = Settings()
        manager = WishManager(settings)

        wishes = manager.load_wishes()

        assert wishes == []

    @patch("builtins.open", new_callable=mock_open)
    def test_load_wishes_with_data(self, mock_file):
        """Test that load_wishes returns the expected wishes when the history file has data."""
        wish1 = {
            "id": "id1",
            "wish": "Wish 1",
            "state": WishState.DONE,
            "created_at": "2023-01-01T00:00:00",
            "finished_at": "2023-01-01T01:00:00",
        }
        wish2 = {
            "id": "id2",
            "wish": "Wish 2",
            "state": WishState.DOING,
            "created_at": "2023-01-02T00:00:00",
            "finished_at": None,
        }
        mock_file.return_value.__enter__.return_value.readlines.return_value = [
            json.dumps(wish1) + "\n",
            json.dumps(wish2) + "\n",
        ]

        settings = Settings()
        manager = WishManager(settings)

        wishes = manager.load_wishes()

        assert len(wishes) == 2
        assert wishes[0].id == "id2"  # Most recent first
        assert wishes[0].wish == "Wish 2"
        assert wishes[0].state == WishState.DOING
        assert wishes[1].id == "id1"
        assert wishes[1].wish == "Wish 1"
        assert wishes[1].state == WishState.DONE

    def test_generate_commands(self):
        """Test that generate_commands returns the expected commands based on the wish text."""
        settings = Settings()
        manager = WishManager(settings)

        # Test with "scan port" in the wish text
        commands = manager.generate_commands("scan port 80")
        assert len(commands) == 2
        assert "nmap" in commands[0]

        # Test with "find suid" in the wish text
        commands = manager.generate_commands("find suid files")
        assert len(commands) == 1
        assert "find / -perm -u=s" in commands[0]

        # Test with "reverse shell" in the wish text
        commands = manager.generate_commands("create a reverse shell")
        assert len(commands) == 3
        assert any("bash -i" in cmd for cmd in commands)

        # Test with other wish text
        commands = manager.generate_commands("some other wish")
        assert len(commands) == 2
        assert any("echo" in cmd for cmd in commands)

    @patch("subprocess.Popen")
    @patch("builtins.open", new_callable=mock_open)
    def test_execute_command(self, mock_open_file, mock_popen):
        """Test that execute_command starts a process and returns a CommandResult."""
        mock_process = MagicMock()
        mock_popen.return_value = mock_process

        settings = Settings()
        manager = WishManager(settings)
        wish = WishDoingFactory.create()
        command = wish.command_results[0].command
        cmd_num = 1

        with patch.object(manager.paths, "create_command_log_dirs") as mock_create_dirs:
            mock_create_dirs.return_value = Path("/path/to/log/dir")

            manager.execute_command(wish, command, cmd_num)
            result = wish.get_command_result_by_num(cmd_num)

            assert result is not None
            assert result.command == command
            assert cmd_num in manager.running_commands
            assert manager.running_commands[cmd_num][0] == mock_process
            assert manager.running_commands[cmd_num][1] == result
            assert manager.running_commands[cmd_num][2] == wish
            assert isinstance(result.log_files, LogFiles)
            assert result.log_files.stdout == Path("/path/to/log/dir") / f"{cmd_num}.stdout"
            assert result.log_files.stderr == Path("/path/to/log/dir") / f"{cmd_num}.stderr"

    @patch("subprocess.Popen")
    @patch("builtins.open", new_callable=mock_open)
    def test_execute_command_exception(self, mock_open_file, mock_popen):
        """Test that execute_command handles exceptions properly."""
        mock_popen.side_effect = Exception("Test exception")

        settings = Settings()
        manager = WishManager(settings)
        wish = WishDoingFactory.create()
        command = wish.command_results[0].command
        cmd_num = 1

        # Mock summarize_log to avoid actual file operations
        with patch.object(manager, "summarize_log") as mock_summarize:
            mock_summarize.return_value = "Test summary"

            with patch.object(manager.paths, "create_command_log_dirs") as mock_create_dirs:
                mock_create_dirs.return_value = Path("/path/to/log/dir")

                manager.execute_command(wish, command, cmd_num)
                result = wish.get_command_result_by_num(cmd_num)

                assert result is not None
                assert result.command == command
                assert result.exit_code == 1
                assert result.state == CommandState.OTHERS
                assert result.finished_at is not None
                assert result.log_summary == "Test summary"
                # Verify summarize_log was called with the log_files
                mock_summarize.assert_called_once_with(result.log_files)

    def test_summarize_log_empty_files(self):
        """Test that summarize_log handles empty log files."""
        settings = Settings()
        manager = WishManager(settings)

        stdout_path = Path("stdout.log")
        stderr_path = Path("stderr.log")
        log_files = LogFiles(stdout=stdout_path, stderr=stderr_path)

        with patch("builtins.open", mock_open(read_data="")) as _m:
            summary = manager.summarize_log(log_files)

            assert "Standard output: <empty>" in summary

    def test_summarize_log_with_content(self):
        """Test that summarize_log summarizes log content correctly."""
        settings = Settings()
        manager = WishManager(settings)

        stdout_path = Path("stdout.log")
        stderr_path = Path("stderr.log")
        log_files = LogFiles(stdout=stdout_path, stderr=stderr_path)

        # Mock file content
        stdout_content = "Line 1\nLine 2\nLine 3"
        stderr_content = "Error 1\nError 2"

        # Create mock context managers for each file
        stdout_mock = MagicMock()
        stdout_mock.__enter__.return_value.read.return_value = stdout_content
        stderr_mock = MagicMock()
        stderr_mock.__enter__.return_value.read.return_value = stderr_content

        # Create a side_effect function to return different mocks for different files
        def mock_open_side_effect(file, *args, **kwargs):
            if str(file) == str(stdout_path):
                return stdout_mock
            elif str(file) == str(stderr_path):
                return stderr_mock
            return MagicMock()

        with patch("builtins.open") as mock_file:
            mock_file.side_effect = mock_open_side_effect

            summary = manager.summarize_log(log_files)

            # Check that the summary contains the expected content
            assert "Standard output:" in summary
            for line in stdout_content.split("\n"):
                assert line in summary
            assert "Standard error:" in summary
            for line in stderr_content.split("\n"):
                assert line in summary

    def test_check_running_commands(self):
        """Test that check_running_commands updates the status of finished commands."""
        settings = Settings()
        manager = WishManager(settings)

        # Create a mock process that has finished
        mock_process = MagicMock()
        mock_process.poll.return_value = 0  # Process has finished
        mock_process.returncode = 0  # Return code 0 (success)

        # Create a command result
        result = CommandResultDoingFactory()

        # Create a wish
        wish = WishDoingFactory.create(command_results=[result])

        # Add to running commands
        manager.running_commands[0] = (mock_process, result, wish)

        # Mock summarize_log
        with patch.object(manager, "summarize_log") as mock_summarize:
            mock_summarize.return_value = "Test summary"

            manager.check_running_commands()

            assert 0 not in manager.running_commands  # Command should be removed
            assert result.exit_code == 0
            assert result.state == CommandState.SUCCESS
            assert result.finished_at is not None
            assert result.log_summary == "Test summary"
            # Verify summarize_log was called with the log_files
            mock_summarize.assert_called_once_with(result.log_files)

    def test_cancel_command(self):
        """Test that cancel_command terminates a running command."""
        settings = Settings()
        manager = WishManager(settings)
        wish = WishDoingFactory.create()

        # Create a mock process
        mock_process = MagicMock()

        # Create a command result
        log_files = LogFilesFactory.create()
        result = CommandResult.create(1, "echo 'test'", log_files)

        # Add to running commands
        cmd_index = 1
        manager.running_commands[cmd_index] = (mock_process, result, wish)

        # Mock time.sleep to avoid actual delay
        with patch("time.sleep"):
            response = manager.cancel_command(wish, cmd_index)

            assert cmd_index not in manager.running_commands
            assert result.state == CommandState.USER_CANCELLED
            assert result.finished_at is not None
            mock_process.terminate.assert_called_once()
            assert "cancelled" in response

    def test_cancel_command_not_running(self):
        """Test that cancel_command handles non-existent command indices."""
        settings = Settings()
        manager = WishManager(settings)
        wish = WishDoingFactory.create()

        response = manager.cancel_command(wish, 999)

        assert "not running" in response

    def test_format_wish_list_item_doing(self):
        """Test that format_wish_list_item formats a wish in DOING state correctly."""
        settings = Settings()
        manager = WishManager(settings)

        wish = WishDoingFactory.create()
        wish.state = WishState.DOING

        formatted = manager.format_wish_list_item(wish, 1)

        assert "[1]" in formatted
        assert wish.wish[:10] in formatted
        assert "doing" in formatted.lower()

    def test_format_wish_list_item_done(self):
        """Test that format_wish_list_item formats a wish in DONE state correctly."""
        settings = Settings()
        manager = WishManager(settings)

        wish = WishDoneFactory.create()

        formatted = manager.format_wish_list_item(wish, 1)

        assert "[1]" in formatted
        assert "done" in formatted.lower()
