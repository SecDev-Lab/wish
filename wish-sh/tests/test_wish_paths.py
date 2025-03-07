from pathlib import Path
from unittest.mock import mock_open, patch

from wish_sh.test_factories.settings_factory import SettingsFactory
from wish_sh.wish_paths import WishPaths


class TestWishPaths:
    def test_initialization(self):
        """Test that WishPaths initializes with the correct attributes."""
        settings = SettingsFactory.create()

        paths = WishPaths(settings)

        assert paths.settings == settings
        assert paths.history_path == Path(settings.WISH_HOME) / "history.jsonl"

    @patch("pathlib.Path.mkdir")
    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.exists")
    def test_ensure_directories(self, mock_exists, mock_file, mock_mkdir):
        """Test that ensure_directories creates the necessary directories and files."""
        mock_exists.return_value = False

        settings = SettingsFactory.create()
        paths = WishPaths(settings)

        paths.ensure_directories()

        # Check that the WISH_HOME directory was created
        mock_mkdir.assert_called_with(parents=True, exist_ok=True)

        # Check that the history file was created if it didn't exist
        mock_file.assert_called_with(paths.history_path, "w")

    def test_get_wish_dir(self):
        """Test that get_wish_dir returns the expected path."""
        settings = SettingsFactory.create()
        paths = WishPaths(settings)
        wish_id = "test_id"

        wish_dir = paths.get_wish_dir(wish_id)

        assert wish_dir == Path(settings.WISH_HOME) / "w" / wish_id

    @patch("pathlib.Path.mkdir")
    def test_create_command_log_dirs(self, mock_mkdir):
        """Test that create_command_log_dirs creates the necessary directories and returns the expected path."""
        settings = SettingsFactory.create()
        paths = WishPaths(settings)
        wish_id = "test_id"

        cmd_log_dir = paths.create_command_log_dirs(wish_id)

        expected_dir = Path(settings.WISH_HOME) / "w" / wish_id / "c" / "log"
        assert cmd_log_dir == expected_dir
        mock_mkdir.assert_called_with(parents=True, exist_ok=True)
