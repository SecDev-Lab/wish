from unittest.mock import MagicMock, patch

from wish_models import WishState

from wish_sh.settings import Settings
from wish_sh.shell_turns import ShellEvent, ShellTurns
from wish_sh.wish_cli import WishCLI
from wish_sh.wish_manager import WishManager


class TestWishCLI:
    def test_initialization(self):
        """Test that WishCLI initializes with the correct attributes."""
        with patch.object(WishManager, "__init__", return_value=None) as mock_manager_init:
            with patch.object(ShellTurns, "register_handler") as mock_register:
                cli = WishCLI()

                assert isinstance(cli.settings, Settings)
                assert cli.running is True
                assert isinstance(cli.state_machine, ShellTurns)
                mock_manager_init.assert_called_once()
                # Verify that all state handlers are registered
                assert mock_register.call_count == 13  # Number of states

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
    @patch("builtins.input", return_value="test wish")
    @patch.object(WishManager, "check_running_commands")
    @patch.object(WishManager, "generate_commands")
    def test_handle_input_wish(self, mock_generate, mock_check, mock_input, mock_print):
        """Test that handle_input_wish processes input correctly."""
        mock_generate.return_value = ["echo 'test'"]

        cli = WishCLI()
        event = cli.handle_input_wish()

        mock_check.assert_called_once()
        mock_generate.assert_called_with("test wish")
        assert event == ShellEvent.SUFFICIENT_WISH
        assert cli.state_machine.get_current_wish() is not None
        assert cli.state_machine.get_current_wish().wish == "test wish"
        assert cli.state_machine.get_current_commands() == ["echo 'test'"]

    @patch("builtins.print")
    @patch("builtins.input", return_value="exit")
    @patch.object(WishManager, "check_running_commands")
    def test_handle_input_wish_exit(self, mock_check, mock_input, mock_print):
        """Test that handle_input_wish handles exit command."""
        cli = WishCLI()
        event = cli.handle_input_wish()

        assert event is None
        assert cli.running is False
        mock_print.assert_any_call("Exiting wish. Goodbye!")

    @patch("builtins.print")
    @patch("builtins.input", return_value="wishlist")
    @patch.object(WishManager, "check_running_commands")
    @patch.object(WishManager, "load_wishes")
    def test_handle_input_wish_wishlist(self, mock_load, mock_check, mock_input, mock_print):
        """Test that handle_input_wish handles wishlist command."""
        mock_load.return_value = [MagicMock(), MagicMock()]

        cli = WishCLI()
        event = cli.handle_input_wish()

        assert event == ShellEvent.CTRL_R
        mock_load.assert_called_once()
        assert len(cli.state_machine.get_wishes()) == 2

    @patch("builtins.print")
    @patch("builtins.input", return_value="scan port 80")
    @patch.object(WishManager, "check_running_commands")
    @patch.object(WishManager, "generate_commands")
    def test_handle_input_wish_insufficient(self, mock_generate, mock_check, mock_input, mock_print):
        """Test that handle_input_wish detects insufficient wish."""
        mock_generate.return_value = ["sudo nmap -p- 10.10.10.40"]

        cli = WishCLI()
        event = cli.handle_input_wish()

        assert event == ShellEvent.INSUFFICIENT_WISH

    @patch("builtins.print")
    @patch("builtins.input", return_value="192.168.1.1")
    def test_handle_ask_wish_detail(self, mock_input, mock_print):
        """Test that handle_ask_wish_detail processes target input."""
        cli = WishCLI()

        # Setup state
        wish = MagicMock()
        commands = ["sudo nmap -p- 10.10.10.40"]
        cli.state_machine.set_current_wish(wish)
        cli.state_machine.set_current_commands(commands)

        event = cli.handle_ask_wish_detail()

        assert event == ShellEvent.OK
        assert cli.state_machine.get_current_commands() == ["sudo nmap -p- 192.168.1.1"]
        mock_print.assert_any_call("\n**What's the target IP address or hostname?**")

    @patch("builtins.print")
    @patch("builtins.input", return_value="y")
    def test_handle_suggest_commands_single(self, mock_input, mock_print):
        """Test that handle_suggest_commands handles single command confirmation."""
        cli = WishCLI()

        # Setup state
        cli.state_machine.set_current_commands(["echo 'test'"])

        event = cli.handle_suggest_commands()

        assert event == ShellEvent.OK
        mock_print.assert_any_call("\nDo you want to execute this command? [Y/n]")

    @patch("builtins.print")
    @patch("builtins.input", return_value="n")
    def test_handle_suggest_commands_multiple_no(self, mock_input, mock_print):
        """Test that handle_suggest_commands handles multiple command rejection."""
        cli = WishCLI()

        # Setup state
        cli.state_machine.set_current_commands(["echo 'test1'", "echo 'test2'"])

        event = cli.handle_suggest_commands()

        assert event == ShellEvent.NO
        mock_print.assert_any_call("\nDo you want to execute all these commands? [Y/n]")

    @patch("builtins.print")
    @patch("builtins.input", return_value="1")
    def test_handle_adjust_commands(self, mock_input, mock_print):
        """Test that handle_adjust_commands processes command selection."""
        cli = WishCLI()

        # Setup state
        commands = ["echo 'test1'", "echo 'test2'", "echo 'test3'"]
        cli.state_machine.set_current_commands(commands)

        event = cli.handle_adjust_commands()

        assert event == ShellEvent.OK
        assert cli.state_machine.get_selected_commands() == ["echo 'test1'"]
        mock_print.assert_any_call("\nSpecify which commands to execute in the format `1`, `1,2` or `1-3`.")

    @patch("builtins.print")
    @patch("builtins.input", return_value="")
    @patch.object(WishManager, "format_wish_list_item")
    def test_handle_show_wishlist_empty(self, mock_format, mock_input, mock_print):
        """Test that handle_show_wishlist handles empty wish list."""
        cli = WishCLI()

        # Setup state
        cli.state_machine.set_wishes([])

        event = cli.handle_show_wishlist()

        assert event == ShellEvent.BACK_TO_INPUT
        mock_print.assert_any_call("No wishes found.")

    @patch("builtins.print")
    @patch("builtins.input", return_value="1")
    @patch.object(WishManager, "format_wish_list_item")
    def test_handle_show_wishlist_select(self, mock_format, mock_input, mock_print):
        """Test that handle_show_wishlist handles wish selection."""
        mock_format.side_effect = ["Formatted Wish 1", "Formatted Wish 2"]

        cli = WishCLI()

        # Setup state
        wishes = [MagicMock(), MagicMock()]
        cli.state_machine.set_wishes(wishes)

        event = cli.handle_show_wishlist()

        assert event == ShellEvent.WISH_NUMBER
        assert cli.state_machine.selected_wish_index == 0
        mock_print.assert_any_call("Formatted Wish 1")
        mock_print.assert_any_call("Formatted Wish 2")

    @patch("builtins.print")
    def test_handle_select_wish(self, mock_print):
        """Test that handle_select_wish displays wish details."""
        cli = WishCLI()

        # Setup state
        wish = MagicMock()
        wish.wish = "Test wish"
        wish.state = WishState.DONE
        wish.created_at = "2023-01-01T00:00:00"
        wish.finished_at = "2023-01-01T01:00:00"

        cli.state_machine.set_wishes([wish])
        cli.state_machine.set_selected_wish_index(0)

        event = cli.handle_select_wish()

        assert event == ShellEvent.OK
        mock_print.assert_any_call("\nWish: Test wish")
        mock_print.assert_any_call(f"Status: {WishState.DONE}")
        mock_print.assert_any_call("Created at: 2023-01-01T00:00:00")
        mock_print.assert_any_call("Finished at: 2023-01-01T01:00:00")

    @patch("builtins.print")
    @patch.object(WishManager, "execute_command")
    @patch.object(WishManager, "save_wish")
    def test_handle_start_commands(self, mock_save, mock_execute, mock_print):
        """Test that handle_start_commands executes commands."""
        mock_execute.return_value = MagicMock()

        cli = WishCLI()

        # Setup state
        wish = MagicMock()
        commands = ["echo 'test1'", "echo 'test2'"]
        cli.state_machine.set_current_wish(wish)
        cli.state_machine.set_current_commands(commands)

        event = cli.handle_start_commands()

        assert event == ShellEvent.BACK_TO_INPUT
        assert mock_execute.call_count == 2
        mock_save.assert_called_once_with(wish)
        mock_print.assert_any_call("\nCommand execution started. Check progress with Ctrl-R or `wishlist`.")

    @patch("builtins.print")
    @patch.object(ShellTurns, "handle_current_state")
    @patch.object(ShellTurns, "transition")
    def test_run(self, mock_transition, mock_handle, mock_print):
        """Test that run executes the state machine correctly."""

        # Setup to make cli.running = False after first event
        def side_effect():
            cli.running = False
            return ShellEvent.OK

        mock_handle.side_effect = side_effect

        cli = WishCLI()
        cli.run()

        assert mock_handle.call_count == 1
        mock_transition.assert_called_once_with(ShellEvent.OK)
        mock_print.assert_any_call("Welcome to wish v0.0.0 - Your wish, our command")
