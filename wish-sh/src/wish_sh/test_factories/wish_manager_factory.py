"""Factory for WishManager."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import factory
from wish_models import CommandState, UtcDatetime

from wish_sh.settings import Settings
from wish_sh.wish_manager import WishManager


class WishManagerFactory(factory.Factory):
    """Factory for WishManager."""

    class Meta:
        model = WishManager

    settings = factory.LazyFunction(lambda: Settings())

    @classmethod
    def create(cls, **kwargs):
        """Create a WishManager instance with mocked file operations."""
        with patch.object(Path, "mkdir"):  # Mock directory creation
            manager = super().create(**kwargs)

            # Initialize running_commands
            manager.running_commands = {}

            return manager

    @classmethod
    def create_with_mock_execute(cls, **kwargs):
        """Create a WishManager with mocked execute_command that actually executes commands."""
        manager = cls.create(**kwargs)

        # Make execute_command actually execute the command
        def execute_command_side_effect(wish, command, cmd_num):
            import subprocess
            from pathlib import Path

            # Create a simple log files structure
            log_files = MagicMock()
            log_files.stdout = Path(f"/tmp/stdout_{cmd_num}.log")
            log_files.stderr = Path(f"/tmp/stderr_{cmd_num}.log")

            # Create a command result
            result = MagicMock()
            result.command = command
            result.state = CommandState.DOING
            result.num = cmd_num
            result.log_files = log_files
            result.exit_code = None
            result.finished_at = None

            # Add the result to the wish
            wish.command_results.append(result)

            # Start the process
            process = subprocess.Popen(command, shell=True)

            # Store in running commands dict
            manager.running_commands[cmd_num] = (process, result, wish)

            return result

        manager.execute_command = MagicMock(side_effect=execute_command_side_effect)

        # Make check_running_commands actually check the commands
        def check_running_commands_side_effect():
            for cmd_num, (process, result, _wish) in list(manager.running_commands.items()):
                if process.poll() is not None:  # Process has finished
                    # Update the result
                    result.state = CommandState.SUCCESS if process.returncode == 0 else CommandState.OTHERS
                    result.exit_code = process.returncode
                    result.finished_at = UtcDatetime.now()

                    # Remove from running commands
                    del manager.running_commands[cmd_num]

        manager.check_running_commands = MagicMock(side_effect=check_running_commands_side_effect)

        return manager

    @classmethod
    def create_with_simple_mocks(cls, **kwargs):
        """Create a WishManager with simple mocked methods."""
        from unittest.mock import MagicMock

        manager = cls.create(**kwargs)

        # Mock methods
        manager.execute_command = MagicMock()
        manager.check_running_commands = MagicMock()
        manager.save_wish = MagicMock()
        manager.generate_commands = MagicMock(return_value=["echo 'Test command 1'", "echo 'Test command 2'"])
        manager.cancel_command = MagicMock(return_value="Command 1 cancelled.")

        # Mock command execution components
        manager.executor = MagicMock()
        manager.executor.execute_commands = MagicMock()
        manager.executor.execute_command = MagicMock()
        manager.executor.check_running_commands = MagicMock()
        manager.executor.cancel_command = MagicMock(return_value="Command 1 cancelled.")

        manager.tracker = MagicMock()
        manager.tracker.check_status = MagicMock()
        manager.tracker.is_all_completed = MagicMock(return_value=(False, False))
        manager.tracker.update_wish_state = MagicMock()
        manager.tracker.get_completion_message = MagicMock(return_value="All commands completed.")

        return manager
