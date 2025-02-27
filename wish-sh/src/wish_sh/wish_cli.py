import sys

from wish_models import Wish, WishState

from wish_sh.settings import Settings
from wish_sh.wish_manager import WishManager


class WishCLI:
    """Command-line interface for wish."""

    def __init__(self):
        self.settings = Settings()
        self.manager = WishManager(self.settings)
        self.running = True

    def print_prompt(self):
        """Print the wish prompt."""
        print("\nwish✨ ", end="", flush=True)

    def print_question(self):
        """Print the question prompt."""
        print("\nwish❓ ", end="", flush=True)

    def handle_wishlist(self):
        """Display the list of wishes."""
        wishes = self.manager.load_wishes()
        if not wishes:
            print("No wishes found.")
            return

        print("")
        for i, wish in enumerate(wishes, 1):
            print(self.manager.format_wish_list_item(wish, i))

        print("\nもっと見る場合はエンターキーを、コマンドの経過・結果を確認したい場合は番号を入力してください。")
        self.print_question()
        choice = input().strip()

        if choice and choice.isdigit():
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(wishes):
                self.handle_wish_details(wishes[choice_idx])
            else:
                print("Invalid selection.")

    def handle_wish_details(self, wish: Wish):
        """Show details for a specific wish."""
        # For prototype, just show a simulated view
        print(f"\nWish: {wish.wish}")
        print(f"Status: {wish.state}")
        print(f"Created at: {wish.created_at}")
        if wish.finished_at:
            print(f"Finished at: {wish.finished_at}")

        # In a real implementation, we'd load and display command results
        # For prototype, show mock data
        print("\nCommands:")
        for i, cmd in enumerate(["find / -perm -u=s -type f 2>/dev/null"], 1):
            print(f"[{i}] cmd: {cmd} ({wish.state})")

        self.print_question()
        choice = input().strip()

        if choice and choice.isdigit():
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

    def execute_wish(self, wish_text: str):
        """Process a wish and execute resulting commands."""
        if not wish_text:
            return

        # Create a new wish
        wish = Wish.create(wish_text)
        wish.state = WishState.DOING
        self.manager.current_wish = wish

        # Generate commands
        commands = self.manager.generate_commands(wish_text)

        # Handle user input for target IP if needed
        if "scan" in wish_text.lower() and "port" in wish_text.lower():
            print("\n**What's the target IP address or hostname?**")
            self.print_question()
            target = input().strip()
            if target:
                commands = [cmd.replace("10.10.10.40", target) for cmd in commands]

        # Display commands and ask for confirmation
        if len(commands) > 1:
            print("\nこのコマンドをすべて実行しますか？ [Y/n]")
            for cmd_num, cmd in enumerate(commands, 1):
                print(f"[{cmd_num}] {cmd}")

            self.print_question()
            confirm = input().strip().lower()

            if confirm == "n":
                print("\nそのまま実行するコマンドを `1` 、 `1,2` または `1-3` の形式で指定してください。")
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
                except:
                    print("Invalid selection format.")
                    return

                # Filter commands based on selection
                if selected_indices:
                    commands = [commands[i] for i in selected_indices if 0 <= i < len(commands)]
                else:
                    print("No valid commands selected.")
                    return
        else:
            # Single command
            print("\nこのコマンドを実行しますか？ [Y/n]")
            print(f"[1] {commands[0]}")

            self.print_question()
            confirm = input().strip().lower()

            if confirm == "n":
                return

        # Execute commands
        print("\nコマンドの実行を開始しました。経過は Ctrl-R または `wishlist` で確認できます。")
        for cmd_num, cmd in enumerate(commands, start=1):
            result = self.manager.execute_command(wish, cmd, cmd_num)

        # Save wish to history
        self.manager.save_wish(wish)

    def run(self):
        """Main loop of the CLI."""
        print("Welcome to wish v0.0.0 - Your wish, our command")

        while self.running:
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
            elif wish_text.lower() == "wishlist":
                self.handle_wishlist()
            else:
                self.execute_wish(wish_text)
