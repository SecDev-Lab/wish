import json
import logging
from pathlib import Path
from typing import List, Optional

from wish_command_execution import CommandExecutor, CommandStatusTracker
from wish_command_execution.backend import BashConfig, create_backend
from wish_command_generation import CommandGenerator
from wish_command_generation.exceptions import CommandGenerationError
from wish_log_analysis import LogAnalysisClient
from wish_models import CommandResult, Settings, Wish, WishState
from wish_models.command_result.command_state import CommandState

from wish_sh.wish_paths import WishPaths


class WishManager:
    """Core functionality for wish."""

    def __init__(self, settings: Settings, backend_config=None):
        """Initialize the wish manager.

        Args:
            settings: Application settings.
            backend_config: Backend configuration (optional).
        """
        self.settings = settings
        self.paths = WishPaths(settings)
        self.paths.ensure_directories()
        self.current_wish: Optional[Wish] = None

        # Initialize command generation component
        self.command_generator = CommandGenerator()

        # Initialize log analysis component
        self.log_analyzer = LogAnalysisClient()

        # Initialize command execution components
        backend = create_backend(backend_config or BashConfig())
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

    def analyze_log(self, command_result: CommandResult) -> CommandResult:
        """Analyze command logs using LogAnalysisClient.

        Args:
            command_result: The command result to analyze.

        Returns:
            The analyzed command result with log_summary and state set.
        """
        try:
            # Analyze using LogAnalysisClient
            analyzed_result = self.log_analyzer.analyze_result(command_result)
            return analyzed_result
        except Exception as e:
            # Log the error
            logging.error(f"Error analyzing log: {str(e)}")

            # Create a copy of the command result with error information
            error_result = CommandResult(
                num=command_result.num,
                command=command_result.command,
                exit_code=command_result.exit_code,
                log_files=command_result.log_files,
                log_summary=f"Error analyzing command: {str(e)}",
                state=CommandState.API_ERROR,
                created_at=command_result.created_at,
                finished_at=command_result.finished_at,
            )

            return error_result

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

    async def generate_commands(self, wish_text: str) -> tuple[List[str], Optional[str]]:
        """Generate commands based on wish text.

        Returns:
            A tuple of (commands, error_message). If error_message is not None,
            it indicates an error occurred during command generation.
        """
        # Create a Wish object
        wish_obj = Wish.create(wish_text)

        try:
            # Get system info directly from the backend
            try:
                # Get system info from the backend
                system_info = await self.executor.backend.get_system_info()
            except Exception as e:
                logging.warning(f"Failed to collect system info: {str(e)}")
                system_info = None

            # Generate commands using CommandGenerator with system info
            command_inputs = self.command_generator.generate_commands(wish_obj, system_info)

            # Add debug logging
            logging.debug(f"Command inputs type: {type(command_inputs)}")
            logging.debug(f"Command inputs: {command_inputs}")
            for i, cmd_input in enumerate(command_inputs):
                logging.debug(f"Command input {i} type: {type(cmd_input)}")
                logging.debug(f"Command input {i}: {cmd_input}")
                if isinstance(cmd_input, dict):
                    logging.debug(f"Command input {i} keys: {cmd_input.keys()}")
                else:
                    logging.debug(f"Command input {i} dir: {dir(cmd_input)}")

            # Extract commands from the result
            commands = []
            for cmd_input in command_inputs:
                if isinstance(cmd_input, dict):
                    commands.append(cmd_input["command"])
                else:
                    commands.append(cmd_input.command)

            return commands, None
        except Exception as e:
            # Handle any errors during command generation
            error_message = f"Error generating commands: {str(e)}"
            logging.error(error_message)

            # Just re-raise CommandGenerationError as is
            if isinstance(e, CommandGenerationError):
                raise

            # Wrap other exceptions in CommandGenerationError
            raise CommandGenerationError(error_message) from e

    # Delegation to CommandExecutor
    async def execute_command(self, wish: Wish, command: str, cmd_num: int):
        """Execute a command and capture its output."""
        await self.executor.execute_command(wish, command, cmd_num)

    async def check_running_commands(self):
        """Check status of running commands and update their status."""
        await self.executor.check_running_commands()

    async def cancel_command(self, wish: Wish, cmd_index: int):
        """Cancel a running command."""
        return await self.executor.cancel_command(wish, cmd_index)

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
