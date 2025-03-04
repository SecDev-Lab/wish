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
            
            # SUGGEST_COMMANDS状態の場合は、Sub Paneにフォーカスを移動
            if self.new_wish_composite.new_wish_turns.current_state == NewWishState.SUGGEST_COMMANDS:
                self.activate_pane("sub-pane")
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
        try:
            # 入力されたwishテキストをmain paneに保存
            self.new_wish_main_pane.set_wish_text(event.wish_text)
            self.logger.debug(f"Saved wish text to main pane: {event.wish_text}")
            
            # 入力を処理
            self.new_wish_composite.handle_wish_input(event.wish_text)
            
            # UIを更新
            self.new_wish_composite.update_for_state()
            
            # SUGGEST_COMMANDS状態の場合は、Sub Paneにフォーカスを移動
            if self.new_wish_composite.new_wish_turns.current_state == NewWishState.SUGGEST_COMMANDS:
                self.activate_pane("sub-pane")
        except Exception as e:
            self.logger.error(f"Error handling WishInputSubmitted: {e}")
    
    def on_wish_detail_submitted(self, event: WishDetailSubmitted) -> None:
        """Handle WishDetailSubmitted message."""
        self.new_wish_composite.handle_wish_detail(event.detail)
        self.new_wish_composite.update_for_state()
        
        # SUGGEST_COMMANDS状態の場合は、Sub Paneにフォーカスを移動
        if self.new_wish_composite.new_wish_turns.current_state == NewWishState.SUGGEST_COMMANDS:
            self.activate_pane("sub-pane")
    
    def on_commands_accepted(self, event: CommandsAccepted) -> None:
        """Handle CommandsAccepted message."""
        self.new_wish_composite.handle_commands_accepted()
        self.new_wish_composite.update_for_state()
    
    def on_commands_rejected(self, event: CommandsRejected) -> None:
        """Handle CommandsRejected message."""
        self.new_wish_composite.handle_commands_rejected()
        self.new_wish_composite.update_for_state()
    
    def on_command_adjust_requested(self, event: CommandAdjustRequested) -> None:
        """Handle CommandAdjustRequested message."""
        self.new_wish_composite.handle_command_adjust_requested()
        self.new_wish_composite.update_for_state()
    
    def on_commands_adjusted(self, event: CommandsAdjusted) -> None:
        """Handle CommandsAdjusted message."""
        self.new_wish_composite.handle_commands_adjusted(event.commands)
        self.new_wish_composite.update_for_state()
        
        # SUGGEST_COMMANDS状態の場合は、Sub Paneにフォーカスを移動
        if self.new_wish_composite.new_wish_turns.current_state == NewWishState.SUGGEST_COMMANDS:
            self.activate_pane("sub-pane")
    
    def on_command_adjust_cancelled(self, event: CommandAdjustCancelled) -> None:
        """Handle CommandAdjustCancelled message."""
        self.new_wish_composite.handle_command_adjust_cancelled()
        self.new_wish_composite.update_for_state()
    
    def on_execution_confirmed(self, event: ExecutionConfirmed) -> None:
        """Handle ExecutionConfirmed message."""
        self.new_wish_composite.handle_execution_confirmed(app=self.app)
        self.new_wish_composite.update_for_state()
    
    def on_execution_cancelled(self, event: ExecutionCancelled) -> None:
        """Handle execution cancelled message."""
        self.new_wish_composite.handle_execution_cancelled()
        self.new_wish_composite.update_for_state()
    
    def _focus_shell_terminal(self) -> None:
        """Focus the shell terminal widget."""
        try:
            # Sub Pane内のシェルターミナルウィジェットを検索
            shell_terminal = None
            
            # まずSub Pane内を検索
            try:
                shell_terminal = self.new_wish_sub_pane.query_one("#shell-terminal", expect_type=ShellTerminalWidget)
                self.logger.debug("Found ShellTerminalWidget in Sub Pane")
            except Exception:
                self.logger.debug("ShellTerminalWidget not found in Sub Pane")
            
            # 見つからなければMain Pane内も検索（後方互換性のため）
            if not shell_terminal:
                try:
                    shell_terminal = self.new_wish_main_pane.query_one("#shell-terminal", expect_type=ShellTerminalWidget)
                    self.logger.debug("Found ShellTerminalWidget in Main Pane")
                except Exception:
                    self.logger.debug("ShellTerminalWidget not found in Main Pane")
            
            # 最後に全体を検索
            if not shell_terminal:
                try:
                    shell_terminal = self.query_one("#shell-terminal", expect_type=ShellTerminalWidget)
                    self.logger.debug("Found ShellTerminalWidget in global scope")
                except Exception:
                    self.logger.debug("ShellTerminalWidget not found in global scope")
            
            if shell_terminal:
                self.logger.debug("Focusing ShellTerminalWidget")
                # フォーカスを設定
                shell_terminal.focus()
                # 確実にフォーカスが設定されるようにタイマーを設定
                self.set_timer(0.1, lambda: self._ensure_shell_terminal_focus(shell_terminal))
            else:
                self.logger.error("ShellTerminalWidget not found anywhere")
        except Exception as e:
            self.logger.error(f"Error focusing ShellTerminalWidget: {e}")
    
    def _focus_shell_terminal_in_sub_pane(self) -> None:
        """Focus the shell terminal widget in the sub pane."""
        try:
            # Sub Pane内のシェルターミナルウィジェットを検索
            shell_terminal = None
            
            # 通常のshell-terminalを検索
            try:
                shell_terminal = self.new_wish_sub_pane.query_one("#shell-terminal", expect_type=ShellTerminalWidget)
                self.logger.debug("Found shell-terminal in Sub Pane")
            except Exception:
                self.logger.debug("shell-terminal not found in Sub Pane")
            
            if shell_terminal:
                self.logger.debug(f"Focusing ShellTerminalWidget in Sub Pane: {shell_terminal.id}")
                # フォーカスを設定
                shell_terminal.focus()
                # 確実にフォーカスが設定されるようにタイマーを設定
                self.set_timer(0.1, lambda: self._ensure_shell_terminal_focus(shell_terminal))
            else:
                self.logger.error("ShellTerminalWidget not found in Sub Pane")
        except Exception as e:
            self.logger.error(f"Error focusing ShellTerminalWidget in Sub Pane: {e}")
    
    def _ensure_shell_terminal_focus(self, shell_terminal=None) -> None:
        """シェルターミナルウィジェットのフォーカスを確実に設定する"""
        try:
            if not shell_terminal:
                # Sub Pane内のシェルターミナルウィジェットを検索
                try:
                    shell_terminal = self.new_wish_sub_pane.query_one("#shell-terminal", expect_type=ShellTerminalWidget)
                except Exception:
                    pass
                
                # 見つからなければMain Pane内も検索
                if not shell_terminal:
                    try:
                        shell_terminal = self.new_wish_main_pane.query_one("#shell-terminal", expect_type=ShellTerminalWidget)
                    except Exception:
                        pass
                
                # 最後に全体を検索
                if not shell_terminal:
                    try:
                        shell_terminal = self.query_one("#shell-terminal", expect_type=ShellTerminalWidget)
                    except Exception:
                        self.logger.error("ShellTerminalWidget not found")
                        return
            
            if shell_terminal:
                self.logger.debug("Ensuring ShellTerminalWidget focus")
                shell_terminal.focus()
                # 現在のフォーカスを確認
                if self.app.focused is not shell_terminal:
                    self.logger.warning(f"ShellTerminalWidget is not focused, current focus: {self.app.focused}")
                    # 再度フォーカスを設定
                    shell_terminal.focus()
        except Exception as e:
            self.logger.error(f"Error ensuring ShellTerminalWidget focus: {e}")
