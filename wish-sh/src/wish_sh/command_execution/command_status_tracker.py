"""Command status tracker for wish_sh."""

from wish_models import CommandState, UtcDatetime, Wish, WishState

from wish_sh.command_execution.command_executor import CommandExecutor


class CommandStatusTracker:
    """Tracks the status of commands for a wish."""

    def __init__(self, wish_manager, executor: CommandExecutor):
        """Initialize the command status tracker.

        Args:
            wish_manager: The WishManager instance providing necessary functionality.
            executor: The CommandExecutor instance to use for checking running commands.
        """
        self.wish_manager = wish_manager
        self.executor = executor
        self.all_completed = False

    def check_status(self, wish: Wish) -> None:
        """Check the status of running commands.

        Args:
            wish: The wish to check the status for.
        """
        self.executor.check_running_commands()

    def is_all_completed(self, wish: Wish) -> tuple[bool, bool]:
        """Check if all commands have completed.

        Args:
            wish: The wish to check the status for.

        Returns:
            A tuple of (all_completed, any_failed).
        """
        all_completed = True
        any_failed = False

        for result in wish.command_results:
            if result.state == CommandState.DOING:
                all_completed = False
                break
            if result.state != CommandState.SUCCESS:
                any_failed = True

        return all_completed, any_failed

    def update_wish_state(self, wish: Wish) -> None:
        """Update the wish state based on command results.

        Args:
            wish: The wish to update the state for.
        """
        all_completed, any_failed = self.is_all_completed(wish)

        if all_completed:
            self.all_completed = True

            # Update wish state
            if any_failed:
                wish.state = WishState.FAILED
            else:
                wish.state = WishState.DONE

            wish.finished_at = UtcDatetime.now()

            # Save wish to history
            self.wish_manager.save_wish(wish)

            return True

        return False

    def get_completion_message(self, wish: Wish) -> str:
        """Get a message indicating the completion status.

        Args:
            wish: The wish to get the completion message for.

        Returns:
            A message indicating the completion status.
        """
        _, any_failed = self.is_all_completed(wish)

        status_text = "All commands completed."
        if any_failed:
            status_text += " Some commands failed."

        return status_text
