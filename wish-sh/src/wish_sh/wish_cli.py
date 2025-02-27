import sys
from typing import Optional

from wish_models import Wish, WishState

from wish_sh.settings import Settings
from wish_sh.shell_turns import ShellEvent, ShellState, ShellTurns
from wish_sh.wish_manager import WishManager


class WishCLI:
    """Command-line interface for wish."""

    def __init__(self):
        self.settings = Settings()
        self.manager = WishManager(self.settings)
        self.running = True
        self.state_machine = ShellTurns()

        # Register state handlers
        self.state_machine.register_handler(ShellState.INPUT_WISH, self.handle_input_wish)
        self.state_machine.register_handler(ShellState.ASK_WISH_DETAIL, self.handle_ask_wish_detail)
        self.state_machine.register_handler(ShellState.SUGGEST_COMMANDS, self.handle_suggest_commands)
        self.state_machine.register_handler(ShellState.CONFIRM_COMMANDS, self.handle_confirm_commands)
        self.state_machine.register_handler(ShellState.ADJUST_COMMANDS, self.handle_adjust_commands)
        self.state_machine.register_handler(ShellState.SHOW_WISHLIST, self.handle_show_wishlist)
        self.state_machine.register_handler(ShellState.SELECT_WISH, self.handle_select_wish)
        self.state_machine.register_handler(ShellState.SHOW_COMMANDS, self.handle_show_commands)
        self.state_machine.register_handler(ShellState.SELECT_COMMAND, self.handle_select_command)
        self.state_machine.register_handler(ShellState.SELECT_COMMANDS, self.handle_select_commands)
        self.state_machine.register_handler(ShellState.SHOW_LOG_SUMMARY, self.handle_show_log_summary)
        self.state_machine.register_handler(ShellState.CANCEL_COMMANDS, self.handle_cancel_commands)
        self.state_machine.register_handler(ShellState.START_COMMANDS, self.handle_start_commands)

    def print_prompt(self):
        """Print the wish prompt."""
        print("\nwish✨ ", end="", flush=True)

    def print_question(self):
        """Print the question prompt."""
        print("\nwish❓ ", end="", flush=True)

    def handle_input_wish(self) -> Optional[ShellEvent]:
        """Handle the INPUT_WISH state."""
        # Check running commands status
        self.manager.check_running_commands()

        # Display prompt and get input
        self.print_prompt()
        try:
            wish_text = input().strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting wish. Goodbye!")
            sys.exit(0)

        # Process input
        if wish_text.lower() == "exit" or wish_text.lower() == "quit":
            print("Exiting wish. Goodbye!")
            self.running = False
            return None
        elif wish_text.lower() == "wishlist":
            # Load wishes for the wishlist state
            wishes = self.manager.load_wishes()
            self.state_machine.set_wishes(wishes)
            return ShellEvent.CTRL_R
        elif not wish_text:
            return None
        else:
            # Create a new wish
            wish = Wish.create(wish_text)
            wish.state = WishState.DOING
            self.state_machine.set_current_wish(wish)

            # Generate commands
            commands = self.manager.generate_commands(wish_text)
            self.state_machine.set_current_commands(commands)

            # Check if we need more details
            if "scan" in wish_text.lower() and "port" in wish_text.lower():
                return ShellEvent.INSUFFICIENT_WISH
            else:
                return ShellEvent.SUFFICIENT_WISH

    def handle_ask_wish_detail(self) -> Optional[ShellEvent]:
        """Handle the ASK_WISH_DETAIL state."""
        commands = self.state_machine.get_current_commands()

        print("\n**What's the target IP address or hostname?**")
        self.print_question()
        target = input().strip()

        if target:
            updated_commands = [cmd.replace("10.10.10.40", target) for cmd in commands]
            self.state_machine.set_current_commands(updated_commands)
            return ShellEvent.OK
        else:
            return ShellEvent.NO

    def handle_suggest_commands(self) -> Optional[ShellEvent]:
        """Handle the SUGGEST_COMMANDS state."""
        commands = self.state_machine.get_current_commands()

        if len(commands) > 1:
            print("\nDo you want to execute all these commands? [Y/n]")
            for cmd_num, cmd in enumerate(commands, 1):
                print(f"[{cmd_num}] {cmd}")

            self.print_question()
            confirm = input().strip().lower()

            if confirm == "n":
                return ShellEvent.NO
            else:
                return ShellEvent.OK
        else:
            # Single command
            print("\nDo you want to execute this command? [Y/n]")
            print(f"[1] {commands[0]}")

            self.print_question()
            confirm = input().strip().lower()

            if confirm == "n":
                return ShellEvent.NO
            else:
                return ShellEvent.OK

    def handle_confirm_commands(self) -> Optional[ShellEvent]:
        """Handle the CONFIRM_COMMANDS state."""
        # This state is for final confirmation before execution
        # In the current implementation, this is merged with SUGGEST_COMMANDS
        # But we keep it separate for future flexibility
        return ShellEvent.OK

    def handle_adjust_commands(self) -> Optional[ShellEvent]:
        """Handle the ADJUST_COMMANDS state."""
        commands = self.state_machine.get_current_commands()

        print("\nSpecify which commands to execute in the format `1`, `1,2` or `1-3`.")
        self.print_question()
        selection = input().strip()

        # Parse selection
        selected_indices = []
        try:
            if "," in selection:
                for part in selection.split(","):
                    if part.strip().isdigit():
                        selected_indices.append(int(part.strip()) - 1)
            elif "-" in selection:
                start, end = selection.split("-")
                selected_indices = list(range(int(start.strip()) - 1, int(end.strip())))
            elif selection.isdigit():
                selected_indices = [int(selection) - 1]
        except Exception as e:
            print(f"Invalid selection format: {e}")
            return ShellEvent.NO

        # Filter commands based on selection
        if selected_indices:
            selected_commands = [commands[i] for i in selected_indices if 0 <= i < len(commands)]
            if selected_commands:
                self.state_machine.set_selected_commands(selected_commands)
                return ShellEvent.OK

        print("No valid commands selected.")
        return ShellEvent.NO

    def handle_show_wishlist(self) -> Optional[ShellEvent]:
        """Handle the SHOW_WISHLIST state."""
        wishes = self.state_machine.get_wishes()

        if not wishes:
            print("No wishes found.")
            return ShellEvent.BACK_TO_INPUT

        print("")
        for i, wish in enumerate(wishes, 1):
            print(self.manager.format_wish_list_item(wish, i))

        print("\nPress Enter to see more, or enter a number to check command progress/results.")
        self.print_question()
        choice = input().strip()

        if choice and choice.isdigit():
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(wishes):
                self.state_machine.set_selected_wish_index(choice_idx)
                return ShellEvent.WISH_NUMBER
            else:
                print("Invalid selection.")
                return ShellEvent.SHOW_MORE
        else:
            return ShellEvent.BACK_TO_INPUT

    def handle_select_wish(self) -> Optional[ShellEvent]:
        """Handle the SELECT_WISH state."""
        wish = self.state_machine.get_selected_wish()

        if not wish:
            return ShellEvent.BACK_TO_INPUT

        print(f"\nWish: {wish.wish}")
        print(f"Status: {wish.state}")
        print(f"Created at: {wish.created_at}")
        if wish.finished_at:
            print(f"Finished at: {wish.finished_at}")

        return ShellEvent.OK

    def handle_show_commands(self) -> Optional[ShellEvent]:
        """Handle the SHOW_COMMANDS state."""
        wish = self.state_machine.get_selected_wish()

        # In a real implementation, we'd load and display command results
        # For prototype, show mock data
        print("\nCommands:")
        for i, cmd in enumerate(["find / -perm -u=s -type f 2>/dev/null"], 1):
            print(f"[{i}] cmd: {cmd} ({wish.state})")

        self.print_question()
        choice = input().strip()

        if choice and choice.isdigit():
            return ShellEvent.MULTIPLE_COMMANDS
        else:
            return ShellEvent.SINGLE_COMMAND

    def handle_select_command(self) -> Optional[ShellEvent]:
        """Handle the SELECT_COMMAND state."""
        wish = self.state_machine.get_selected_wish()

        print("\n(Simulating log output for prototype)")
        if wish.state == WishState.DONE:
            print("\nLog Summary:")
            print("/usr/bin/sudo")
            print("/usr/bin/passwd")
            print("/usr/bin/chfn")
            print("...")
            print(f"\nDetails are available in log files under {self.manager.paths.get_wish_dir(wish.id)}/c/log/")
        else:
            print("\n(Simulating tail -f output)")
            print("/usr/bin/sudo")
            print("/usr/bin/passwd")
            print("...")

        return ShellEvent.OK

    def handle_select_commands(self) -> Optional[ShellEvent]:
        """Handle the SELECT_COMMANDS state."""
        # This state is for selecting multiple commands from a list
        # In the current implementation, this is handled in other states
        return ShellEvent.OK

    def handle_show_log_summary(self) -> Optional[ShellEvent]:
        """Handle the SHOW_LOG_SUMMARY state."""
        # This state is for showing log summary
        # In the current implementation, this is handled in SELECT_COMMAND
        return ShellEvent.BACK_TO_INPUT

    def handle_cancel_commands(self) -> Optional[ShellEvent]:
        """Handle the CANCEL_COMMANDS state."""
        print("Commands cancelled.")
        return ShellEvent.BACK_TO_INPUT

    def handle_start_commands(self) -> Optional[ShellEvent]:
        """Handle the START_COMMANDS state."""
        wish = self.state_machine.get_current_wish()
        commands = self.state_machine.get_current_commands()

        if not wish or not commands:
            return ShellEvent.BACK_TO_INPUT

        # Execute commands
        print("\nCommand execution started. Check progress with Ctrl-R or `wishlist`.")
        for cmd_num, cmd in enumerate(commands, start=1):
            self.manager.execute_command(wish, cmd, cmd_num)

        # Save wish to history
        self.manager.current_wish = wish
        self.manager.save_wish(wish)

        return ShellEvent.BACK_TO_INPUT

    def run(self):
        """Main loop of the CLI."""
        print("Welcome to wish v0.0.0 - Your wish, our command")

        while self.running:
            event = self.state_machine.handle_current_state()
            if event:
                self.state_machine.transition(event)
