import json
import subprocess
import time
from typing import Dict, List, Optional, Tuple

from wish_models import CommandResult, CommandState, LogFiles, Wish, WishState

from wish_sh.command_generation import CommandGenerator, MockCommandGenerator, LlmCommandGenerator
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
        
        # 設定に基づいてコマンドジェネレーターを初期化
        if hasattr(settings, 'use_llm') and settings.use_llm and hasattr(settings, 'llm_api_key') and settings.llm_api_key:
            self.command_generator = LlmCommandGenerator(settings.llm_api_key, getattr(settings, 'llm_model', 'gpt-4'))
        else:
            self.command_generator = MockCommandGenerator()

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
        """Generate commands based on wish text."""
        return self.command_generator.generate_commands(wish_text)

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

            except subprocess.SubprocessError as e:
                error_msg = f"サブプロセスエラー: {str(e)}"
                stderr_file.write(error_msg)
                self._handle_command_failure(result, wish, 1, CommandState.OTHERS, error_msg)
                
            except PermissionError as e:
                error_msg = f"権限エラー: コマンド '{command}' の実行権限がありません"
                stderr_file.write(error_msg)
                self._handle_command_failure(result, wish, 126, CommandState.OTHERS, error_msg)
                
            except FileNotFoundError as e:
                error_msg = f"コマンドが見つかりません: '{command}'"
                stderr_file.write(error_msg)
                self._handle_command_failure(result, wish, 127, CommandState.OTHERS, error_msg)
                
            except Exception as e:
                error_msg = f"予期せぬエラー: {str(e)}"
                stderr_file.write(error_msg)
                self._handle_command_failure(result, wish, 1, CommandState.OTHERS, error_msg)

    def _handle_command_failure(self, result: CommandResult, wish: Wish, exit_code: int, state: CommandState, log_summary: str):
        """共通のコマンド失敗処理."""
        result.finish(
            exit_code=exit_code,
            state=state,
            log_summarizer=lambda _: log_summary
        )
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
