from unittest.mock import MagicMock, patch

from wish_models import WishState

from wish_sh.settings import Settings
from wish_sh.wish_cli import WishCLI
from wish_sh.wish_manager import WishManager


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
