"""Composite pattern implementation for panes in wish-sh TUI."""

from abc import ABC, abstractmethod
from typing import Optional, List

from textual.message import Message

from wish_models import Wish, CommandResult
from wish_sh.logging import setup_logger
from wish_sh.tui.new_wish_turns import NewWishTurns, NewWishState, NewWishEvent
from wish_sh.tui.widgets.base_pane import BasePane


class PaneComposite(ABC):
    """Abstract base class for pane composites."""

    def __init__(self, main_pane: BasePane, sub_pane: BasePane):
        """Initialize the PaneComposite.

        Args:
            main_pane: The main pane.
            sub_pane: The sub pane.
        """
        self.main_pane = main_pane
        self.sub_pane = sub_pane
        self.logger = setup_logger(f"wish_sh.tui.{self.__class__.__name__}")

    @abstractmethod
    def update_for_mode(self) -> None:
        """Update panes for the current mode."""
        pass

    def handle_key_event(self, event) -> bool:
        """Handle key events.

        Args:
            event: The key event.

        Returns:
            bool: True if the event was handled, False otherwise.
        """
        return False

    def set_active_pane(self, pane_id: str) -> None:
        """Set the active pane.

        Args:
            pane_id: The ID of the pane to activate.
        """
        # Deactivate all panes first
        self.main_pane.set_active(False)
        self.sub_pane.set_active(False)

        # Then activate the specified pane
        if pane_id == "main-pane":
            self.main_pane.set_active(True)
        elif pane_id == "sub-pane":
            self.sub_pane.set_active(True)


class WishHistoryPaneComposite(PaneComposite):
    """Composite for wish history mode panes."""

    def __init__(self, main_pane: BasePane, sub_pane: BasePane):
        """Initialize the WishHistoryPaneComposite.

        Args:
            main_pane: The main pane.
            sub_pane: The sub pane.
        """
        super().__init__(main_pane, sub_pane)
        self.current_wish = None

    def update_for_mode(self) -> None:
        """Update panes for wish history mode."""
        self.main_pane.update_for_wish_history_mode()
        self.sub_pane.update_for_wish_history_mode()

    def update_wish(self, wish: Optional[Wish], preserve_selection: bool = False) -> None:
        """Update the panes with the selected wish details.

        Args:
            wish: The wish to display.
            preserve_selection: Whether to preserve the current selection.
        """
        self.current_wish = wish
        self.main_pane.update_wish(wish, preserve_selection)

        # If wish has commands, display the first command by default
        if wish and wish.command_results and len(wish.command_results) > 0:
            self.display_command(wish.command_results[0])
        else:
            self.sub_pane.clear_command_output()

    def display_command(self, command_result: CommandResult) -> None:
        """Display command details in the sub pane.

        Args:
            command_result: The command result to display.
        """
        if command_result:
            self.sub_pane.update_command_output(command_result)

    def handle_key_event(self, event) -> bool:
        """Handle key events for command selection.

        Args:
            event: The key event.

        Returns:
            bool: True if the event was handled, False otherwise.
        """
        # Delegate to the active pane
        if self.main_pane.has_class("active-pane"):
            return self.main_pane.on_key(event)
        elif self.sub_pane.has_class("active-pane"):
            return self.sub_pane.on_key(event)
        return False


class NewWishPaneComposite(PaneComposite):
    """Composite for new wish mode panes."""

    def __init__(self, main_pane: BasePane, sub_pane: BasePane):
        """Initialize the NewWishPaneComposite.

        Args:
            main_pane: The main pane.
            sub_pane: The sub pane.
        """
        super().__init__(main_pane, sub_pane)
        self.new_wish_turns = NewWishTurns()

    def update_for_mode(self) -> None:
        """Update panes for new wish mode."""
        # Reset NewWishTurns to initial state
        self.new_wish_turns.current_state = NewWishState.INPUT_WISH
        self.update_for_state()

    def update_for_state(self) -> None:
        """Update UI based on current NewWishState."""
        current_state = self.new_wish_turns.current_state

        if current_state == NewWishState.INPUT_WISH:
            self.main_pane.update_for_input_wish()
            self.sub_pane.update_for_input_wish()

        elif current_state == NewWishState.ASK_WISH_DETAIL:
            self.main_pane.update_for_ask_wish_detail()
            self.sub_pane.update_for_ask_wish_detail()

        elif current_state == NewWishState.SUGGEST_COMMANDS:
            commands = self.new_wish_turns.get_current_commands()
            # ログ出力を追加
            from wish_sh.logging import setup_logger
            logger = setup_logger("wish_sh.tui.NewWishPaneComposite")
            logger.debug(f"SUGGEST_COMMANDS state: commands={commands}")
            
            # Main Paneを更新
            self.main_pane.update_for_suggest_commands(commands)
            logger.debug("Main Pane updated")
            
            # Sub Paneを更新
            try:
                self.sub_pane.update_for_suggest_commands(commands)
                logger.debug("Sub Pane updated")
            except Exception as e:
                logger.error(f"Error updating Sub Pane: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")

        elif current_state == NewWishState.ADJUST_COMMANDS:
            commands = self.new_wish_turns.get_current_commands()
            # ログ出力を追加
            from wish_sh.logging import setup_logger
            logger = setup_logger("wish_sh.tui.NewWishPaneComposite")
            logger.debug(f"ADJUST_COMMANDS state: commands={commands}")
            
            # Main Paneを更新
            self.main_pane.update_for_adjust_commands(commands)
            logger.debug("Main Pane updated for ADJUST_COMMANDS")
            
            # Sub Paneを更新
            try:
                self.sub_pane.update_for_adjust_commands(commands)
                logger.debug("Sub Pane updated for ADJUST_COMMANDS")
            except Exception as e:
                logger.error(f"Error updating Sub Pane for ADJUST_COMMANDS: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")

        elif current_state == NewWishState.CONFIRM_COMMANDS:
            commands = self.new_wish_turns.get_selected_commands() or self.new_wish_turns.get_current_commands()
            # ログ出力を追加
            from wish_sh.logging import setup_logger
            logger = setup_logger("wish_sh.tui.NewWishPaneComposite")
            logger.debug(f"CONFIRM_COMMANDS state: commands={commands}")
            
            # Main Paneを更新
            self.main_pane.update_for_confirm_commands(commands)
            logger.debug("Main Pane updated for CONFIRM_COMMANDS")
            
            # Sub Paneを更新
            try:
                self.sub_pane.update_for_confirm_commands(commands)
                logger.debug("Sub Pane updated for CONFIRM_COMMANDS")
            except Exception as e:
                logger.error(f"Error updating Sub Pane for CONFIRM_COMMANDS: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")

        elif current_state == NewWishState.EXECUTE_COMMANDS:
            commands = self.new_wish_turns.get_selected_commands() or self.new_wish_turns.get_current_commands()
            # ログ出力を追加
            from wish_sh.logging import setup_logger
            logger = setup_logger("wish_sh.tui.NewWishPaneComposite")
            logger.debug(f"EXECUTE_COMMANDS state: commands={commands}")
            
            # Main Paneを更新
            self.main_pane.update_for_execute_commands(commands)
            logger.debug("Main Pane updated for EXECUTE_COMMANDS")
            
            # Sub Paneを更新
            try:
                self.sub_pane.update_for_execute_commands(commands)
                logger.debug("Sub Pane updated for EXECUTE_COMMANDS")
            except Exception as e:
                logger.error(f"Error updating Sub Pane for EXECUTE_COMMANDS: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")

    def handle_wish_input(self, wish_text: str) -> None:
        """Handle wish input.

        Args:
            wish_text: The wish text.
        """
        self.logger.debug(f"NewWishPaneComposite handling wish input: '{wish_text}'")
        self.logger.debug(f"DEBUGGING: NewWishPaneComposite handling wish input: '{wish_text}'")
        
        try:
            # Analyze the wish content
            self.logger.debug("DEBUGGING: About to check if wish is sufficient")
            if self.is_wish_sufficient(wish_text):
                self.logger.debug("Wish is sufficient, proceeding to command suggestion")
                self.logger.debug("DEBUGGING: Wish is sufficient, proceeding to command suggestion")
                # If there is sufficient information, proceed to command suggestion
                from wish_models import Wish

                self.logger.debug("DEBUGGING: About to create Wish object")
                wish = Wish.create(wish_text)
                self.logger.debug(f"Created wish: {wish}")
                self.logger.debug(f"DEBUGGING: Created wish: {wish}")
                self.new_wish_turns.set_current_wish(wish)
                self.logger.debug("DEBUGGING: Set current wish")

                # Generate commands
                from wish_sh.wish_manager import WishManager
                from wish_sh.settings import Settings

                self.logger.debug("DEBUGGING: Creating WishManager")
                manager = WishManager(Settings())
                self.logger.debug("Generating commands")
                self.logger.debug("DEBUGGING: About to generate commands")
                commands = manager.generate_commands(wish_text)
                self.logger.debug(f"Generated commands: {commands}")
                self.logger.debug(f"DEBUGGING: Generated commands: {commands}")
                self.new_wish_turns.set_current_commands(commands)
                self.logger.debug("DEBUGGING: Set current commands")
                
                # State transition
                self.logger.debug("Transitioning to SUFFICIENT_WISH state")
                self.logger.debug("DEBUGGING: About to transition to SUFFICIENT_WISH state")
                self.new_wish_turns.transition(NewWishEvent.SUFFICIENT_WISH)
                self.logger.debug(f"New state: {self.new_wish_turns.current_state}")
                self.logger.debug(f"DEBUGGING: New state: {self.new_wish_turns.current_state}")
            else:
                self.logger.debug("Wish is insufficient, proceeding to detail input")
                self.logger.debug("DEBUGGING: Wish is insufficient, proceeding to detail input")
                # If information is insufficient, proceed to detail input
                from wish_models import Wish

                wish = Wish.create(wish_text)
                self.logger.debug(f"Created wish: {wish}")
                self.logger.debug(f"DEBUGGING: Created wish: {wish}")
                self.new_wish_turns.set_current_wish(wish)
                self.logger.debug("DEBUGGING: Set current wish")

                # State transition
                self.logger.debug("Transitioning to INSUFFICIENT_WISH state")
                self.logger.debug("DEBUGGING: About to transition to INSUFFICIENT_WISH state")
                self.new_wish_turns.transition(NewWishEvent.INSUFFICIENT_WISH)
                self.logger.debug(f"New state: {self.new_wish_turns.current_state}")
                self.logger.debug(f"DEBUGGING: New state: {self.new_wish_turns.current_state}")

            # Update UI
            self.logger.debug("Updating UI for new state")
            self.logger.debug("DEBUGGING: About to update UI for new state")
            self.update_for_state()
            self.logger.debug("UI updated successfully")
            self.logger.debug("DEBUGGING: UI updated successfully")
        except Exception as e:
            self.logger.error(f"Error in handle_wish_input: {e}")
            self.logger.error(f"DEBUGGING: Error in handle_wish_input: {e}")
            import traceback
            self.logger.error(f"DEBUGGING: Traceback: {traceback.format_exc()}")

    def is_wish_sufficient(self, wish_text: str) -> bool:
        """Determine if the wish has sufficient information.

        Args:
            wish_text: The wish text

        Returns:
            bool: Whether there is sufficient information
        """
        # In actual implementation, more complex determination logic would be needed
        if "scan" in wish_text.lower() and "port" in wish_text.lower():
            # For port scanning, a target IP is required
            return "10.10.10" in wish_text or "192.168" in wish_text
        return True

    def handle_wish_detail(self, detail: str) -> None:
        """Handle wish detail.

        Args:
            detail: The wish detail.
        """
        self.new_wish_turns.set_wish_detail(detail)

        # Get current wish and commands
        wish = self.new_wish_turns.get_current_wish()
        if wish:
            # Update wish
            wish.wish = f"{wish.wish} on {detail}"
            self.new_wish_turns.set_current_wish(wish)

            # Update commands
            from wish_sh.wish_manager import WishManager
            from wish_sh.settings import Settings

            manager = WishManager(Settings())
            commands = manager.generate_commands(wish.wish)
            self.new_wish_turns.set_current_commands(commands)

        # State transition
        self.new_wish_turns.transition(NewWishEvent.DETAIL_PROVIDED)

        # Update UI
        self.update_for_state()

    def handle_commands_accepted(self) -> None:
        """Handle commands accepted."""
        # State transition
        self.new_wish_turns.transition(NewWishEvent.COMMANDS_ACCEPTED)

        # Update UI
        self.update_for_state()

    def handle_commands_rejected(self) -> None:
        """Handle commands rejected."""
        # State transition
        self.new_wish_turns.transition(NewWishEvent.COMMANDS_REJECTED)

        # Update UI
        self.update_for_state()

    def handle_command_adjust_requested(self) -> None:
        """Handle command adjust requested."""
        # State transition
        self.new_wish_turns.transition(NewWishEvent.ADJUSTMENT_REQUESTED)

        # Update UI
        self.update_for_state()

    def handle_commands_adjusted(self, commands: List[str]) -> None:
        """Handle commands adjusted.

        Args:
            commands: The adjusted commands.
        """
        # Set adjusted commands
        self.new_wish_turns.set_selected_commands(commands)

        # State transition
        self.new_wish_turns.transition(NewWishEvent.COMMANDS_ADJUSTED)

        # Update UI
        self.update_for_state()

    def handle_command_adjust_cancelled(self) -> None:
        """Handle command adjust cancelled."""
        # State transition
        self.new_wish_turns.transition(NewWishEvent.BACK_TO_INPUT)

        # Update UI
        self.update_for_state()

    def handle_execution_confirmed(self, app=None) -> None:
        """Handle execution confirmed.
        
        Args:
            app: The application instance.
        """
        # State transition
        self.new_wish_turns.transition(NewWishEvent.EXECUTION_CONFIRMED)

        # Execute commands
        wish = self.new_wish_turns.get_current_wish()
        commands = self.new_wish_turns.get_selected_commands() or self.new_wish_turns.get_current_commands()

        if wish and commands:
            # Execute commands
            from wish_sh.wish_manager import WishManager
            from wish_sh.settings import Settings
            from wish_sh.tui.widgets.shell_terminal_widget import ShellTerminalWidget

            # Get shell terminal widget
            if not app:
                self.logger.error("DEBUGGING: App instance not available")
                return
                
            try:
                shell_terminal = app.query_one("#shell-terminal", expect_type=ShellTerminalWidget)
                if not shell_terminal:
                    self.logger.error("DEBUGGING: ShellTerminalWidget not found")
                    return
            except Exception as e:
                self.logger.error(f"DEBUGGING: Error finding ShellTerminalWidget: {e}")
                import traceback
                self.logger.error(f"DEBUGGING: Traceback: {traceback.format_exc()}")
                return

            manager = WishManager(Settings())
            for cmd_num, cmd in enumerate(commands, start=1):
                # Display command in shell terminal
                if shell_terminal:
                    shell_terminal.add_output(f"\nExecuting: {cmd}\n")

                # Execute command
                result = manager.execute_command(wish, cmd, cmd_num)

                # Display results in shell terminal
                if shell_terminal and result:
                    if result.stdout:
                        shell_terminal.add_output(f"Standard output:\n{result.stdout}\n")
                    if result.stderr:
                        shell_terminal.add_output(f"Standard error:\n{result.stderr}\n")
                    shell_terminal.add_output(f"Exit code: {result.return_code}\n")

            # Save wish
            manager.current_wish = wish
            manager.save_wish(wish)

            # Display completion message in shell terminal
            if shell_terminal:
                shell_terminal.add_output("\nAll commands have been executed.\n")

        # Update UI
        self.update_for_state()

    def handle_execution_cancelled(self) -> None:
        """Handle execution cancelled."""
        # State transition
        self.new_wish_turns.transition(NewWishEvent.EXECUTION_CANCELLED)

        # Update UI
        self.update_for_state()
