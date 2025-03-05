"""Command executor for wish_sh."""

from wish_models import Wish
from wish_sh.wish_manager import WishManager


class CommandExecutor:
    """Executes commands for a wish."""

    def __init__(self, wish_manager: WishManager):
        """Initialize the command executor.
        
        Args:
            wish_manager: The WishManager instance to use for executing commands.
        """
        self.wish_manager = wish_manager

    def execute_commands(self, wish: Wish, commands: list[str]) -> None:
        """Execute a list of commands for a wish.
        
        Args:
            wish: The wish to execute commands for.
            commands: The list of commands to execute.
        """
        for i, cmd in enumerate(commands, 1):
            self.execute_command(wish, cmd, i)

    def execute_command(self, wish: Wish, command: str, cmd_num: int) -> None:
        """Execute a single command for a wish.
        
        Args:
            wish: The wish to execute the command for.
            command: The command to execute.
            cmd_num: The command number.
        """
        self.wish_manager.execute_command(wish, command, cmd_num)

    def cancel_command(self, wish: Wish, cmd_num: int) -> str:
        """Cancel a running command.
        
        Args:
            wish: The wish to cancel the command for.
            cmd_num: The command number to cancel.
            
        Returns:
            A message indicating the result of the cancellation.
        """
        return self.wish_manager.cancel_command(wish, cmd_num)
