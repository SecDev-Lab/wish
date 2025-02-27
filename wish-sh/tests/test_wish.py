import json
import os
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

from wish_models.test_factories import CommandResultSuccessFactory, LogFilesFactory, WishDoingFactory, WishDoneFactory

from wish_sh import (
    CommandResult,
    LogFiles,
    Settings,
    WishCLI,
    WishManager,
    WishPaths,
    WishState,
)
from wish_sh import (
    CommandState as CommandState,
)


class TestSettings:
    def test_initialization_with_default(self):
        """Test that Settings initializes with the default WISH_HOME when environment variable is not set."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            expected_default = os.path.join(os.path.expanduser("~"), ".wish")
            assert settings.WISH_HOME == expected_default

    def test_initialization_with_env_var(self):
        """Test that Settings initializes with the WISH_HOME from environment variable when it is set."""
        custom_wish_home = "/custom/wish/home"
        with patch.dict(os.environ, {"WISH_HOME": custom_wish_home}, clear=True):
            settings = Settings()
            assert settings.WISH_HOME == custom_wish_home


class TestWishPaths:
    def test_initialization(self):
        """Test that WishPaths initializes with the correct attributes."""
        settings = Settings()

        paths = WishPaths(settings)

        assert paths.settings == settings
        assert paths.history_path == Path(settings.WISH_HOME) / "history.jsonl"

    @patch("pathlib.Path.mkdir")
    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.exists")
    def test_ensure_directories(self, mock_exists, mock_file, mock_mkdir):
        """Test that ensure_directories creates the necessary directories and files."""
        mock_exists.return_value = False

        settings = Settings()
        paths = WishPaths(settings)

        paths.ensure_directories()

        # Check that the WISH_HOME directory was created
        mock_mkdir.assert_called_with(parents=True, exist_ok=True)

        # Check that the history file was created if it didn't exist
        mock_file.assert_called_with(paths.history_path, "w")

    def test_get_wish_dir(self):
        """Test that get_wish_dir returns the expected path."""
        settings = Settings()
        paths = WishPaths(settings)
        wish_id = "test_id"

        wish_dir = paths.get_wish_dir(wish_id)

        assert wish_dir == Path(settings.WISH_HOME) / "w" / wish_id

    @patch("pathlib.Path.mkdir")
    def test_create_command_log_dirs(self, mock_mkdir):
        """Test that create_command_log_dirs creates the necessary directories and returns the expected path."""
        settings = Settings()
        paths = WishPaths(settings)
        wish_id = "test_id"

        cmd_log_dir = paths.create_command_log_dirs(wish_id)

        expected_dir = Path(settings.WISH_HOME) / "w" / wish_id / "c" / "log"
        assert cmd_log_dir == expected_dir
        mock_mkdir.assert_called_with(parents=True, exist_ok=True)


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

            result = manager.execute_command(wish, command, cmd_num)

            assert result.command == command
            assert cmd_num in manager.running_commands
            assert manager.running_commands[cmd_num][0] == mock_process
            assert manager.running_commands[cmd_num][1] == result
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

        with patch.object(manager.paths, "create_command_log_dirs") as mock_create_dirs:
            mock_create_dirs.return_value = Path("/path/to/log/dir")

            result = manager.execute_command(wish, command, cmd_num)

            assert result.command == command
            assert result.exit_code == 1
            assert result.state == CommandState.OTHERS
            assert result.finished_at is not None

    def test_summarize_log_empty_files(self):
        """Test that summarize_log handles empty log files."""
        settings = Settings()
        manager = WishManager(settings)

        stdout_path = Path("stdout.log")
        stderr_path = Path("stderr.log")

        with patch("builtins.open", mock_open(read_data="")) as m:
            summary = manager.summarize_log(stdout_path, stderr_path)

            assert "Standard output: <empty>" in summary

    def test_summarize_log_with_content(self):
        """Test that summarize_log summarizes log content correctly."""
        settings = Settings()
        manager = WishManager(settings)

        stdout_path = Path("stdout.log")
        stderr_path = Path("stderr.log")

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

            summary = manager.summarize_log(stdout_path, stderr_path)

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
        result = CommandResultSuccessFactory()

        # Add to running commands
        manager.running_commands[0] = (mock_process, result)

        # Mock summarize_log
        with patch.object(manager, "summarize_log") as mock_summarize:
            mock_summarize.return_value = "Test summary"

            manager.check_running_commands()

            assert 0 not in manager.running_commands  # Command should be removed
            assert result.exit_code == 0
            assert result.state == CommandState.SUCCESS
            assert result.finished_at is not None
            assert result.log_summary == "Test summary"

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
        manager.running_commands[cmd_index] = (mock_process, result)

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


class TestWishCLI:
    def test_initialization(self):
        """Test that WishCLI initializes with the correct attributes."""
        with patch.object(WishManager, "__init__", return_value=None) as mock_manager_init:
            cli = WishCLI()

            assert isinstance(cli.settings, Settings)
            assert cli.running is True
            mock_manager_init.assert_called_once()

    @patch("builtins.print")
    def test_print_prompt(self, mock_print):
        """Test that print_prompt prints the expected prompt."""
        cli = WishCLI()

        cli.print_prompt()

        mock_print.assert_called_with("\nwish✨ ", end="", flush=True)

    @patch("builtins.print")
    def test_print_question(self, mock_print):
        """Test that print_question prints the expected prompt."""
        cli = WishCLI()

        cli.print_question()

        mock_print.assert_called_with("\nwish❓ ", end="", flush=True)

    @patch("builtins.print")
    @patch("builtins.input", return_value="")
    @patch.object(WishManager, "load_wishes")
    def test_handle_wishlist_empty(self, mock_load_wishes, mock_input, mock_print):
        """Test that handle_wishlist handles empty wish list correctly."""
        mock_load_wishes.return_value = []

        cli = WishCLI()
        cli.handle_wishlist()

        mock_load_wishes.assert_called_once()
        mock_print.assert_any_call("No wishes found.")

    @patch("builtins.print")
    @patch("builtins.input", return_value="")
    @patch.object(WishManager, "load_wishes")
    @patch.object(WishManager, "format_wish_list_item")
    def test_handle_wishlist_with_wishes(self, mock_format, mock_load_wishes, mock_input, mock_print):
        """Test that handle_wishlist displays wishes correctly."""
        wish1 = MagicMock()
        wish2 = MagicMock()
        mock_load_wishes.return_value = [wish1, wish2]
        mock_format.side_effect = ["Formatted Wish 1", "Formatted Wish 2"]

        cli = WishCLI()
        cli.handle_wishlist()

        mock_load_wishes.assert_called_once()
        assert mock_format.call_count == 2
        mock_print.assert_any_call("Formatted Wish 1")
        mock_print.assert_any_call("Formatted Wish 2")

    @patch("builtins.print")
    @patch("builtins.input", return_value="1")
    @patch.object(WishManager, "load_wishes")
    @patch.object(WishCLI, "handle_wish_details")
    @patch.object(WishManager, "format_wish_list_item")
    def test_handle_wishlist_select_wish(
        self, mock_format, mock_handle_details, mock_load_wishes, mock_input, mock_print
    ):
        """Test that handle_wishlist handles wish selection correctly."""
        wish1 = MagicMock()
        wish2 = MagicMock()
        mock_load_wishes.return_value = [wish1, wish2]
        mock_format.side_effect = ["Formatted Wish 1", "Formatted Wish 2"]

        cli = WishCLI()
        cli.handle_wishlist()

        mock_handle_details.assert_called_with(wish1)

    @patch("builtins.print")
    @patch("builtins.input", side_effect=["", ""])
    def test_handle_wish_details(self, mock_input, mock_print):
        """Test that handle_wish_details displays wish details correctly."""
        wish = MagicMock()
        wish.wish = "Test wish"
        wish.state = WishState.DONE
        wish.created_at = "2023-01-01T00:00:00"
        wish.finished_at = "2023-01-01T01:00:00"

        cli = WishCLI()
        cli.handle_wish_details(wish)

        mock_print.assert_any_call("\nWish: Test wish")
        mock_print.assert_any_call(f"Status: {WishState.DONE}")
        mock_print.assert_any_call("Created at: 2023-01-01T00:00:00")
        mock_print.assert_any_call("Finished at: 2023-01-01T01:00:00")

    @patch("builtins.print")
    @patch("builtins.input", return_value="y")
    @patch.object(WishManager, "generate_commands")
    @patch.object(WishManager, "execute_command")
    @patch.object(WishManager, "save_wish")
    def test_execute_wish_single_command(self, mock_save, mock_execute, mock_generate, mock_input, mock_print):
        """Test that execute_wish handles a single command correctly."""
        mock_generate.return_value = ["echo 'test'"]
        mock_execute.return_value = MagicMock()

        cli = WishCLI()
        cli.execute_wish("Test wish")

        mock_generate.assert_called_with("Test wish")
        mock_execute.assert_called_once()
        mock_save.assert_called_once()
        assert cli.manager.current_wish.wish == "Test wish"
        assert cli.manager.current_wish.state == WishState.DOING

    @patch("builtins.print")
    @patch("builtins.input", side_effect=["n", "1"])
    @patch.object(WishManager, "generate_commands")
    @patch.object(WishManager, "execute_command")
    @patch.object(WishManager, "save_wish")
    def test_execute_wish_multiple_commands_select_one(
        self, mock_save, mock_execute, mock_generate, mock_input, mock_print
    ):
        """Test that execute_wish handles command selection correctly."""
        mock_generate.return_value = ["echo 'test1'", "echo 'test2'"]
        mock_execute.return_value = MagicMock()

        cli = WishCLI()
        cli.execute_wish("Test wish")

        mock_generate.assert_called_with("Test wish")
        mock_execute.assert_called_once()
        mock_save.assert_called_once()

    @patch("builtins.print")
    @patch("builtins.input", return_value="n")
    def test_execute_wish_cancel(self, mock_input, mock_print):
        """Test that execute_wish handles cancellation correctly."""
        cli = WishCLI()
        cli.execute_wish("")

        # Should return early without doing anything
        mock_print.assert_not_called()

    @patch("builtins.print")
    @patch("sys.exit")
    def test_run_keyboard_interrupt(self, mock_exit, mock_print):
        """Test that run handles KeyboardInterrupt correctly."""
        cli = WishCLI()

        # Mock the input function to raise KeyboardInterrupt
        with patch("builtins.input", side_effect=KeyboardInterrupt):
            # We only need to test that sys.exit is called with the correct argument
            # and that the correct message is printed
            # We don't need to run the full method since it would try to access wish_text
            # which is not defined when KeyboardInterrupt is raised
            try:
                cli.run()
            except UnboundLocalError:
                # This is expected because wish_text is not defined
                pass

        mock_exit.assert_called_with(0)
        mock_print.assert_any_call("\nExiting wish. Goodbye!")

    @patch("builtins.print")
    @patch("builtins.input", return_value="exit")
    @patch.object(WishManager, "check_running_commands")
    def test_run_exit_command(self, mock_check, mock_input, mock_print):
        """Test that run handles exit command correctly."""
        cli = WishCLI()
        cli.run()

        assert cli.running is False
        mock_print.assert_any_call("Exiting wish. Goodbye!")

    @patch("builtins.print")
    @patch("builtins.input", side_effect=["wishlist", "exit"])
    @patch.object(WishCLI, "handle_wishlist")
    @patch.object(WishManager, "check_running_commands")
    def test_run_wishlist_command(self, mock_check, mock_handle_wishlist, mock_input, mock_print):
        """Test that run handles wishlist command correctly."""
        cli = WishCLI()
        cli.run()

        mock_handle_wishlist.assert_called_once()

    @patch("builtins.print")
    @patch("builtins.input", side_effect=["some wish", "exit"])
    @patch.object(WishCLI, "execute_wish")
    @patch.object(WishManager, "check_running_commands")
    def test_run_execute_wish(self, mock_check, mock_execute_wish, mock_input, mock_print):
        """Test that run handles wish execution correctly."""
        cli = WishCLI()
        cli.run()

        mock_execute_wish.assert_called_with("some wish")


# Test for main function
@patch.object(WishCLI, "run")
def test_main(mock_run):
    """Test that main function creates a WishCLI instance and runs it."""
    from wish_sh import main

    main()

    mock_run.assert_called_once()
