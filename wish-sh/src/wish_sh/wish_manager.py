import json
from pathlib import Path
from typing import List, Optional

from wish_command_execution import CommandExecutor, CommandStatusTracker
from wish_command_execution.backend import BashBackend
from wish_models import LogFiles, Wish, WishState

from wish_sh.command_generation import LlmCommandGenerator, MockCommandGenerator
from wish_sh.settings import Settings
from wish_sh.wish_paths import WishPaths


class WishManager:
    """Core functionality for wish."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.paths = WishPaths(settings)
        self.paths.ensure_directories()
        self.current_wish: Optional[Wish] = None

        # Initialize command generator based on settings
        if (hasattr(settings, 'use_llm') and settings.use_llm and
                hasattr(settings, 'llm_api_key') and settings.llm_api_key):
            self.command_generator = LlmCommandGenerator(
                settings.llm_api_key, getattr(settings, 'llm_model', 'gpt-4')
            )
        else:
            self.command_generator = MockCommandGenerator()

        # Initialize command execution components
        backend = BashBackend(log_summarizer=self.summarize_log)
        self.executor = CommandExecutor(backend=backend, log_dir_creator=self.create_command_log_dirs)
        self.tracker = CommandStatusTracker(self.executor, wish_saver=self.save_wish)

    # Functions required for command execution
    def create_command_log_dirs(self, wish_id: str) -> Path:
        """Create command log directories."""
        return self.paths.create_command_log_dirs(wish_id)

    def save_wish(self, wish: Wish):
        """Save wish to history file."""
        with open(self.paths.history_path, "a") as f:
            f.write(json.dumps(wish.to_dict()) + "\n")

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

    # WishManager functions
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
        """Generate commands based on wish text."""
        return self.command_generator.generate_commands(wish_text)

    # Delegation to CommandExecutor
    def execute_command(self, wish: Wish, command: str, cmd_num: int):
        """Execute a command and capture its output."""
        self.executor.execute_command(wish, command, cmd_num)

    def check_running_commands(self):
        """Check status of running commands and update their status."""
        self.executor.check_running_commands()

    def cancel_command(self, wish: Wish, cmd_index: int):
        """Cancel a running command."""
        return self.executor.cancel_command(wish, cmd_index)

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
