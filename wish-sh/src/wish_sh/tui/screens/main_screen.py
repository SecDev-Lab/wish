"""Main screen for wish-sh TUI."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.screen import Screen

from wish_sh.logging import setup_logger
from wish_sh.settings import Settings
from wish_sh.wish_manager import WishManager
from wish_sh.tui.modes import WishMode
from wish_sh.tui.new_wish_turns import NewWishState, NewWishEvent, NewWishTurns
from wish_sh.tui.new_wish_messages import (
    WishInputSubmitted,
    WishDetailSubmitted,
    CommandsAccepted,
    CommandsRejected,
    CommandAdjustRequested,
    CommandsAdjusted,
    CommandAdjustCancelled,
    ExecutionConfirmed,
    ExecutionCancelled,
)
from wish_sh.tui.widgets.help_pane import HelpPane
from wish_sh.tui.widgets.pane_composite import PaneComposite, WishHistoryPaneComposite, NewWishPaneComposite
from wish_sh.tui.widgets.wish_history_main_pane import WishHistoryMainPane, CommandSelected
from wish_sh.tui.widgets.wish_history_sub_pane import WishHistorySubPane
from wish_sh.tui.widgets.new_wish_main_pane import NewWishMainPane
from wish_sh.tui.widgets.new_wish_sub_pane import NewWishSubPane
from wish_sh.tui.widgets.wish_select_pane import WishSelectPane, WishSelected
from wish_sh.tui.widgets.shell_terminal_widget import ShellTerminalWidget


class ActivatePane(Message):
    """Message sent to request activation of a specific pane."""

    def __init__(self, pane_id: str):
        """Initialize the message.
        
        Args:
            pane_id: The ID of the pane to activate.
        """
        self.pane_id = pane_id
        super().__init__()


class MainScreen(Screen):
    """Main screen for the wish-sh TUI application."""
    
    def __init__(self, *args, wish_manager=None, **kwargs):
        """Initialize the MainScreen."""
        super().__init__(*args, **kwargs)
        # Set up logger
        self.logger = setup_logger("wish_sh.tui.MainScreen")
        
        # Initialize with dependency injection
        self.settings = Settings()
        self.manager = wish_manager or WishManager(self.settings)
        # Load past wishes
        self.wishes = self.manager.load_wishes()
        # Initialize with NEW_WISH mode by default
        self.current_mode = WishMode.NEW_WISH
        
        # Initialize NewWishTurns for state management
        self.new_wish_turns = NewWishTurns()

    # CSS moved to external file: wish_tui.css

    def compose(self) -> ComposeResult:
        """Compose the screen."""
        # Create the main layout
        self.wish_select = WishSelectPane(wishes=self.wishes, manager=self.manager, id="wish-select")
        self.help_pane = HelpPane(id="help-pane")
        
        # Create mode-specific panes
        self.wish_history_main_pane = WishHistoryMainPane(id="wish-history-main-pane")
        self.wish_history_sub_pane = WishHistorySubPane(id="wish-history-sub-pane")
        self.new_wish_main_pane = NewWishMainPane(id="new-wish-main-pane")
        self.new_wish_sub_pane = NewWishSubPane(id="new-wish-sub-pane")
        
        # Create composites
        self.wish_history_composite = WishHistoryPaneComposite(
            self.wish_history_main_pane, 
            self.wish_history_sub_pane
        )
        self.new_wish_composite = NewWishPaneComposite(
            self.new_wish_main_pane,
            self.new_wish_sub_pane
        )
        
        # Set active composite based on initial mode
        self.active_composite = self.new_wish_composite
        
        # Yield the widgets in the desired order
        yield self.wish_select
        yield self.wish_history_main_pane
        yield self.wish_history_sub_pane
        yield self.new_wish_main_pane
        yield self.new_wish_sub_pane
        yield self.help_pane
        
        # Import New Wish widgets
        from wish_sh.tui.widgets.new_wish_widgets import (
            WishInputForm,
            WishDetailForm,
            CommandSuggestForm,
            CommandAdjustForm,
            CommandConfirmForm,
            CommandExecuteStatus,
        )
        
        # Create New Wish widgets but don't mount them yet
        self.wish_input_form = WishInputForm(id="wish-input-form")
        self.wish_detail_form = WishDetailForm(id="wish-detail-form")
        # Other widgets will be created dynamically when needed

    def on_mount(self) -> None:
        """Event handler called when the screen is mounted."""
        # Hide inactive panes
        self.wish_history_main_pane.display = False
        self.wish_history_sub_pane.display = False
        
        # Set initial focus to the main pane
        self.new_wish_main_pane.focus()
        
        # Set initial active state
        self.wish_select.set_active(False)
        self.new_wish_main_pane.set_active(True)
        self.new_wish_sub_pane.set_active(False)
        
        # Update help text for initial active pane
        self.help_pane.update_help("main-pane")
        
        # Hide all forms initially
        self._unmount_new_wish_forms()
        
        # Initialize with NEW_WISH mode
        self.set_mode(WishMode.NEW_WISH)
    
    def on_key(self, event) -> None:
        """Handle key events."""
        # Log key events at debug level
        self.logger.debug(f"Key event: {event.key}")
        # 現在のモードに応じて適切なペインの状態をログに出力
        if self.current_mode == WishMode.NEW_WISH:
            self.logger.debug(f"Active pane: wish_select={self.wish_select.has_class('active-pane')}, "
                             f"main_pane={self.new_wish_main_pane.has_class('active-pane')}, "
                             f"sub_pane={self.new_wish_sub_pane.has_class('active-pane')}")
        else:
            self.logger.debug(f"Active pane: wish_select={self.wish_select.has_class('active-pane')}, "
                             f"main_pane={self.wish_history_main_pane.has_class('active-pane')}, "
                             f"sub_pane={self.wish_history_sub_pane.has_class('active-pane')}")
        self.logger.debug(f"Current mode: {self.current_mode}")
        
        # Log Ctrl+Down key events
        if event.key in ("ctrl+down", "ctrl+arrow_down", "down+ctrl"):
            self.logger.debug(f"Ctrl+Down key detected: {event.key}")
        
        # Handle up/down keys when Wish Select pane is active
        if self.wish_select.has_class("active-pane"):
            if event.key in ("up", "arrow_up"):
                self.logger.debug("Passing up key to wish_select")
                self.wish_select.select_previous()
                return True  # Consume event
            elif event.key in ("down", "arrow_down"):
                self.logger.debug("Passing down key to wish_select")
                self.wish_select.select_next()
                return True  # Consume event
        
        # Delegate key events to the active composite
        if self.active_composite and self.active_composite.handle_key_event(event):
            return True  # Consume event if the composite handled it
        
        # Navigate between panes with arrow keys
        if event.key in ("left", "arrow_left"):
            self.activate_pane("wish-select")
            return True  # Consume event
        elif event.key in ("right", "arrow_right"):
            self.activate_pane("main-pane")
            return True  # Consume event
        # Use Ctrl+arrow keys for vertical navigation
        elif event.key in ("ctrl+up", "ctrl+arrow_up", "up+ctrl"):
            self.activate_pane("main-pane")
            return True  # Consume event
        elif event.key in ("ctrl+down", "ctrl+arrow_down", "down+ctrl"):
            self.activate_pane("sub-pane")
            return True  # Consume event
    
    def activate_pane(self, pane_id: str) -> None:
        """Activate the specified pane."""
        # Deactivate all panes
        self.wish_select.set_active(False)
        self.wish_history_main_pane.set_active(False)
        self.wish_history_sub_pane.set_active(False)
        self.new_wish_main_pane.set_active(False)
        self.new_wish_sub_pane.set_active(False)
        
        # Activate the specified pane
        if pane_id == "wish-select":
            self.wish_select.set_active(True)
            self.wish_select.focus()
        elif pane_id in ("main-pane", "sub-pane"):
            # Delegate to the active composite
            self.active_composite.set_active_pane(pane_id)
        
        # Update help text based on active pane
        self.help_pane.update_help(pane_id)
    
    def display_command(self, command_result):
        """Display command details in the sub pane.
        
        Args:
            command_result: The command result to display.
        """
        if command_result and isinstance(self.active_composite, WishHistoryPaneComposite):
            self.active_composite.display_command(command_result)
    
    def set_mode(self, mode: WishMode, wish=None) -> None:
        """Set the current mode and update panes accordingly.
        
        Args:
            mode: The mode to set.
            wish: The wish to display (for WISH_HISTORY mode).
        """
        self.current_mode = mode
        
        # Hide all panes first
        self.wish_history_main_pane.display = False
        self.wish_history_sub_pane.display = False
        self.new_wish_main_pane.display = False
        self.new_wish_sub_pane.display = False
        
        if mode == WishMode.NEW_WISH:
            # Show NEW WISH panes
            self.new_wish_main_pane.display = True
            self.new_wish_sub_pane.display = True
            
            # Set active composite
            self.active_composite = self.new_wish_composite
            
            # Update panes for NEW WISH mode
            self.active_composite.update_for_mode()
            
            # Update New Wish UI to show input form
            self.update_new_wish_ui()
        else:
            # Show WISH HISTORY panes
            self.wish_history_main_pane.display = True
            self.wish_history_sub_pane.display = True
            
            # Set active composite
            self.active_composite = self.wish_history_composite
            
            # Update panes for WISH HISTORY mode
            self.active_composite.update_for_mode()
            
            # Update wish if provided
            if wish:
                self.active_composite.update_wish(wish)
    
    def update_new_wish_ui(self) -> None:
        """Update UI based on current NewWishState."""
        # Import New Wish widgets
        from wish_sh.tui.widgets.new_wish_widgets import (
            WishInputForm,
            WishDetailForm,
            CommandSuggestForm,
            CommandAdjustForm,
            CommandConfirmForm,
            CommandExecuteStatus,
        )
        from wish_sh.tui.widgets.shell_terminal_widget import ShellTerminalWidget
        
        # 現在のフォームをアンマウント
        self._unmount_new_wish_forms()
        
        # 現在の状態に応じてUIを更新
        current_state = self.new_wish_composite.new_wish_turns.current_state
        
        # 現在の状態に応じてUIを更新
        if current_state == NewWishState.INPUT_WISH:
            # 一意のIDを生成するために現在時刻のタイムスタンプを使用
            import time
            unique_id = f"wish-input-form-{int(time.time())}"
            self.logger.debug(f"Creating WishInputForm with unique ID: {unique_id}")
            
            # WishInputFormをマウント
            self.wish_input_form = WishInputForm(id=unique_id)
            self.new_wish_main_pane.mount(self.wish_input_form)
            
            # ShellTerminalWidgetにフォーカスを設定
            self.logger.debug("Setting focus to ShellTerminalWidget")
            self.call_after_refresh(self._focus_shell_terminal)
            
        elif current_state == NewWishState.ASK_WISH_DETAIL:
            # 一意のIDを生成するために現在時刻のタイムスタンプを使用
            import time
            unique_id = f"wish-detail-form-{int(time.time())}"
            self.logger.debug(f"Creating WishDetailForm with unique ID: {unique_id}")
            
            # WishDetailFormをマウント
            self.wish_detail_form = WishDetailForm(id=unique_id)
            self.new_wish_main_pane.mount(self.wish_detail_form)
            
        elif current_state == NewWishState.SUGGEST_COMMANDS:
            commands = self.new_wish_composite.new_wish_turns.get_current_commands()
            
            # 一意のIDを生成するために現在時刻のタイムスタンプを使用
            import time
            unique_id = f"command-suggest-form-{int(time.time())}"
            self.logger.debug(f"Creating CommandSuggestForm with unique ID: {unique_id}")
            
            # CommandSuggestFormをマウント
            self.command_suggest_form = CommandSuggestForm(commands, id=unique_id)
            self.new_wish_main_pane.mount(self.command_suggest_form)
            
        elif current_state == NewWishState.ADJUST_COMMANDS:
            commands = self.new_wish_composite.new_wish_turns.get_current_commands()
            
            # 一意のIDを生成するために現在時刻のタイムスタンプを使用
            import time
            unique_id = f"command-adjust-form-{int(time.time())}"
            self.logger.debug(f"Creating CommandAdjustForm with unique ID: {unique_id}")
            
            # CommandAdjustFormをマウント
            self.command_adjust_form = CommandAdjustForm(commands, id=unique_id)
            self.new_wish_main_pane.mount(self.command_adjust_form)
            
        elif current_state == NewWishState.CONFIRM_COMMANDS:
            commands = self.new_wish_composite.new_wish_turns.get_selected_commands() or self.new_wish_composite.new_wish_turns.get_current_commands()
            
            # 一意のIDを生成するために現在時刻のタイムスタンプを使用
            import time
            unique_id = f"command-confirm-form-{int(time.time())}"
            self.logger.debug(f"Creating CommandConfirmForm with unique ID: {unique_id}")
            
            # CommandConfirmFormをマウント
            self.command_confirm_form = CommandConfirmForm(commands, id=unique_id)
            self.new_wish_main_pane.mount(self.command_confirm_form)
            
        elif current_state == NewWishState.EXECUTE_COMMANDS:
            commands = self.new_wish_composite.new_wish_turns.get_selected_commands() or self.new_wish_composite.new_wish_turns.get_current_commands()
            
            # 一意のIDを生成するために現在時刻のタイムスタンプを使用
            import time
            unique_id = f"command-execute-status-{int(time.time())}"
            self.logger.debug(f"Creating CommandExecuteStatus with unique ID: {unique_id}")
            
            # CommandExecuteStatusをマウント
            self.command_execute_status = CommandExecuteStatus(commands, id=unique_id)
            self.new_wish_main_pane.mount(self.command_execute_status)
    
    def _unmount_new_wish_forms(self) -> None:
        """Unmount all New Wish forms."""
        # 直接new_wish_main_paneの子ウィジェットをチェックして、フォームをアンマウント
        try:
            # 既存のフォームを削除
            if hasattr(self, "wish_input_form") and self.wish_input_form.parent:
                self.logger.debug(f"Removing wish_input_form")
                self.wish_input_form.remove()
            
            if hasattr(self, "wish_detail_form") and self.wish_detail_form.parent:
                self.logger.debug(f"Removing wish_detail_form")
                self.wish_detail_form.remove()
            
            if hasattr(self, "command_suggest_form") and hasattr(self.command_suggest_form, "parent") and self.command_suggest_form.parent:
                self.logger.debug(f"Removing command_suggest_form")
                self.command_suggest_form.remove()
            
            if hasattr(self, "command_adjust_form") and hasattr(self.command_adjust_form, "parent") and self.command_adjust_form.parent:
                self.logger.debug(f"Removing command_adjust_form")
                self.command_adjust_form.remove()
            
            if hasattr(self, "command_confirm_form") and hasattr(self.command_confirm_form, "parent") and self.command_confirm_form.parent:
                self.logger.debug(f"Removing command_confirm_form")
                self.command_confirm_form.remove()
            
            if hasattr(self, "command_execute_status") and hasattr(self.command_execute_status, "parent") and self.command_execute_status.parent:
                self.logger.debug(f"Removing command_execute_status")
                self.command_execute_status.remove()
            
            # 念のため、new_wish_main_paneの子ウィジェットをチェックして、フォームをアンマウント
            children = list(self.new_wish_main_pane._nodes)
            for child in children:
                # main-pane-content以外のウィジェットをアンマウント
                if child.id != "main-pane-content" and child.id.endswith("-form"):
                    self.logger.debug(f"Removing widget with ID: {child.id}")
                    child.remove()
        except Exception as e:
            self.logger.error(f"Error in _unmount_new_wish_forms: {e}")
    
    def on_wish_selected(self, event: WishSelected) -> None:
        """Handle wish selection events."""
        self.set_mode(event.mode, event.wish)
    
    def on_command_selected(self, event: CommandSelected) -> None:
        """Handle command selection events."""
        # Update the sub pane with command output but keep focus on main pane
        self.display_command(event.command_result)
        
    def on_activate_pane(self, event: ActivatePane) -> None:
        """Handle pane activation requests."""
        self.activate_pane(event.pane_id)
    
    # New Wish mode message handlers
    def on_wish_input_submitted(self, event: WishInputSubmitted) -> None:
        """Handle WishInputSubmitted message."""
        self.new_wish_composite.handle_wish_input(event.wish_text)
        self.update_new_wish_ui()
    
    def on_wish_detail_submitted(self, event: WishDetailSubmitted) -> None:
        """Handle WishDetailSubmitted message."""
        self.new_wish_composite.handle_wish_detail(event.detail)
        self.update_new_wish_ui()
    
    def on_commands_accepted(self, event: CommandsAccepted) -> None:
        """Handle CommandsAccepted message."""
        self.new_wish_composite.handle_commands_accepted()
        self.update_new_wish_ui()
    
    def on_commands_rejected(self, event: CommandsRejected) -> None:
        """Handle CommandsRejected message."""
        self.new_wish_composite.handle_commands_rejected()
        self.update_new_wish_ui()
    
    def on_command_adjust_requested(self, event: CommandAdjustRequested) -> None:
        """Handle CommandAdjustRequested message."""
        self.new_wish_composite.handle_command_adjust_requested()
        self.update_new_wish_ui()
    
    def on_commands_adjusted(self, event: CommandsAdjusted) -> None:
        """Handle CommandsAdjusted message."""
        self.new_wish_composite.handle_commands_adjusted(event.commands)
        self.update_new_wish_ui()
    
    def on_command_adjust_cancelled(self, event: CommandAdjustCancelled) -> None:
        """Handle CommandAdjustCancelled message."""
        self.new_wish_composite.handle_command_adjust_cancelled()
        self.update_new_wish_ui()
    
    def on_execution_confirmed(self, event: ExecutionConfirmed) -> None:
        """Handle ExecutionConfirmed message."""
        self.new_wish_composite.handle_execution_confirmed()
        self.update_new_wish_ui()
    
    def on_execution_cancelled(self, event: ExecutionCancelled) -> None:
        """Handle execution cancelled message."""
        self.new_wish_composite.handle_execution_cancelled()
        self.update_new_wish_ui()
    
    def _focus_shell_terminal(self) -> None:
        """Focus the shell terminal widget."""
        try:
            shell_terminal = self.query_one("#shell-terminal", expect_type=ShellTerminalWidget)
            if shell_terminal:
                self.logger.debug("Focusing ShellTerminalWidget")
                shell_terminal.focus()
        except Exception as e:
            self.logger.error(f"Error focusing ShellTerminalWidget: {e}")
