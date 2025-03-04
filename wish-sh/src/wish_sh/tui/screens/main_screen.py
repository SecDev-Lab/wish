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
        self.logger.debug(f"Updating UI for state: {current_state}")
        
        # 現在の状態に応じてUIを更新
        if current_state == NewWishState.INPUT_WISH:
            # テスト用に固定のIDを使用
            self.logger.debug(f"Creating WishInputForm with ID: wish-input-form")
            
            # WishInputFormをマウント
            self.wish_input_form = WishInputForm(id="wish-input-form")
            
            # 既存のフォームを確実に削除
            try:
                # 既存のフォームを削除
                for child in list(self.new_wish_main_pane._nodes):
                    if child.id == "wish-input-form":
                        self.logger.debug(f"Removing existing form: {child.id}")
                        child.remove()
            except Exception as e:
                self.logger.error(f"Error removing existing forms: {e}")
            
            # 新しいフォームをMain Paneにマウント
            try:
                self.new_wish_main_pane.mount(self.wish_input_form)
            except Exception as e:
                self.logger.error(f"Error mounting wish_input_form: {e}")
                # 既存のフォームが残っている場合は、それを使用
                try:
                    # expect_noneではなくexpect_typeを使用
                    try:
                        existing_form = self.new_wish_main_pane.query_one("#wish-input-form")
                        # 既存のフォームが見つかった場合は、何もしない
                        self.logger.debug(f"Using existing form: {existing_form.id}")
                    except Exception:
                        # フォームが見つからない場合は、新しいフォームを作成して再度マウント
                        self.logger.debug("Creating new form with unique ID")
                        import uuid
                        unique_id = f"wish-input-form-{uuid.uuid4().hex}"
                        self.wish_input_form = WishInputForm(id=unique_id)
                        self.new_wish_main_pane.mount(self.wish_input_form)
                except Exception as e2:
                    self.logger.error(f"Error handling form mounting fallback: {e2}")
                    import traceback
                    self.logger.error(f"Traceback: {traceback.format_exc()}")
            
            # ShellTerminalWidgetにフォーカスを設定
            self.logger.debug("Setting focus to ShellTerminalWidget")
            self.call_after_refresh(self._focus_shell_terminal)
            
            # 確実にフォーカスが設定されるように複数回試行
            self.set_timer(0.2, self._focus_shell_terminal)
            self.set_timer(0.5, self._focus_shell_terminal)
            self.set_timer(1.0, self._focus_shell_terminal)
            
        elif current_state == NewWishState.ASK_WISH_DETAIL:
            # 一意のIDを生成するためにUUIDを使用
            import uuid
            unique_id = f"wish-detail-form-{uuid.uuid4().hex}"
            self.logger.debug(f"Creating WishDetailForm with unique ID: {unique_id}")
            
            # 既存のフォームが完全に削除されたことを確認
            try:
                existing_forms = self.new_wish_main_pane.query("WishDetailForm")
                for form in existing_forms:
                    self.logger.debug(f"Removing existing form: {form.id}")
                    form.remove()
            except Exception as e:
                self.logger.error(f"Error removing existing forms: {e}")
            
            # WishDetailFormをMain Paneにマウント
            self.wish_detail_form = WishDetailForm(id=unique_id)
            self.new_wish_main_pane.mount(self.wish_detail_form)
            
        elif current_state == NewWishState.SUGGEST_COMMANDS:
            commands = self.new_wish_composite.new_wish_turns.get_current_commands()
            
            # 一意のIDを生成するためにUUIDを使用
            import uuid
            unique_id = f"command-suggest-form-{uuid.uuid4().hex}"
            self.logger.debug(f"Creating CommandSuggestForm with unique ID: {unique_id}")
            
            # 既存のフォームが完全に削除されたことを確認
            try:
                existing_forms = self.new_wish_main_pane.query("CommandSuggestForm")
                for form in existing_forms:
                    self.logger.debug(f"Removing existing form: {form.id}")
                    form.remove()
            except Exception as e:
                self.logger.error(f"Error removing existing forms: {e}")
            
            # CommandSuggestFormをMain Paneにマウント
            self.command_suggest_form = CommandSuggestForm(commands, id=unique_id)
            self.new_wish_main_pane.mount(self.command_suggest_form)
            
        elif current_state == NewWishState.ADJUST_COMMANDS:
            commands = self.new_wish_composite.new_wish_turns.get_current_commands()
            
            # 一意のIDを生成するためにUUIDを使用
            import uuid
            unique_id = f"command-adjust-form-{uuid.uuid4().hex}"
            self.logger.debug(f"Creating CommandAdjustForm with unique ID: {unique_id}")
            
            # 既存のフォームが完全に削除されたことを確認
            try:
                existing_forms = self.new_wish_main_pane.query("CommandAdjustForm")
                for form in existing_forms:
                    self.logger.debug(f"Removing existing form: {form.id}")
                    form.remove()
            except Exception as e:
                self.logger.error(f"Error removing existing forms: {e}")
            
            # CommandAdjustFormをMain Paneにマウント
            self.command_adjust_form = CommandAdjustForm(commands, id=unique_id)
            self.new_wish_main_pane.mount(self.command_adjust_form)
            
        elif current_state == NewWishState.CONFIRM_COMMANDS:
            commands = self.new_wish_composite.new_wish_turns.get_selected_commands() or self.new_wish_composite.new_wish_turns.get_current_commands()
            
            # 一意のIDを生成するためにUUIDを使用
            import uuid
            unique_id = f"command-confirm-form-{uuid.uuid4().hex}"
            self.logger.debug(f"Creating CommandConfirmForm with unique ID: {unique_id}")
            
            # 既存のフォームが完全に削除されたことを確認
            try:
                existing_forms = self.new_wish_main_pane.query("CommandConfirmForm")
                for form in existing_forms:
                    self.logger.debug(f"Removing existing form: {form.id}")
                    form.remove()
            except Exception as e:
                self.logger.error(f"Error removing existing forms: {e}")
            
            # CommandConfirmFormをMain Paneにマウント
            self.command_confirm_form = CommandConfirmForm(commands, id=unique_id)
            self.new_wish_main_pane.mount(self.command_confirm_form)
            
        elif current_state == NewWishState.EXECUTE_COMMANDS:
            commands = self.new_wish_composite.new_wish_turns.get_selected_commands() or self.new_wish_composite.new_wish_turns.get_current_commands()
            
            # 一意のIDを生成するためにUUIDを使用
            import uuid
            unique_id = f"command-execute-status-{uuid.uuid4().hex}"
            self.logger.debug(f"Creating CommandExecuteStatus with unique ID: {unique_id}")
            
            # 既存のフォームが完全に削除されたことを確認
            try:
                existing_forms = self.new_wish_main_pane.query("CommandExecuteStatus")
                for form in existing_forms:
                    self.logger.debug(f"Removing existing form: {form.id}")
                    form.remove()
            except Exception as e:
                self.logger.error(f"Error removing existing forms: {e}")
            
            # CommandExecuteStatusをMain Paneにマウント
            self.command_execute_status = CommandExecuteStatus(commands, id=unique_id)
            self.new_wish_main_pane.mount(self.command_execute_status)
    
    def _unmount_new_wish_forms(self) -> None:
        """Unmount all New Wish forms."""
        try:
            # 既存のフォームを削除
            # 属性の存在チェックと親チェックを分離して、より堅牢にする
            if hasattr(self, "wish_input_form"):
                try:
                    if self.wish_input_form.parent:
                        self.logger.debug(f"Removing wish_input_form")
                        self.wish_input_form.remove()
                except Exception as e:
                    self.logger.error(f"Error removing wish_input_form: {e}")
                # 属性を削除
                delattr(self, "wish_input_form")
            
            if hasattr(self, "wish_detail_form"):
                try:
                    if self.wish_detail_form.parent:
                        self.logger.debug(f"Removing wish_detail_form")
                        self.wish_detail_form.remove()
                except Exception as e:
                    self.logger.error(f"Error removing wish_detail_form: {e}")
                # 属性を削除
                delattr(self, "wish_detail_form")
            
            if hasattr(self, "command_suggest_form"):
                try:
                    if hasattr(self.command_suggest_form, "parent") and self.command_suggest_form.parent:
                        self.logger.debug(f"Removing command_suggest_form")
                        self.command_suggest_form.remove()
                except Exception as e:
                    self.logger.error(f"Error removing command_suggest_form: {e}")
                # 属性を削除
                delattr(self, "command_suggest_form")
            
            if hasattr(self, "command_adjust_form"):
                try:
                    if hasattr(self.command_adjust_form, "parent") and self.command_adjust_form.parent:
                        self.logger.debug(f"Removing command_adjust_form")
                        self.command_adjust_form.remove()
                except Exception as e:
                    self.logger.error(f"Error removing command_adjust_form: {e}")
                # 属性を削除
                delattr(self, "command_adjust_form")
            
            if hasattr(self, "command_confirm_form"):
                try:
                    if hasattr(self.command_confirm_form, "parent") and self.command_confirm_form.parent:
                        self.logger.debug(f"Removing command_confirm_form")
                        self.command_confirm_form.remove()
                except Exception as e:
                    self.logger.error(f"Error removing command_confirm_form: {e}")
                # 属性を削除
                delattr(self, "command_confirm_form")
            
            if hasattr(self, "command_execute_status"):
                try:
                    if hasattr(self.command_execute_status, "parent") and self.command_execute_status.parent:
                        self.logger.debug(f"Removing command_execute_status")
                        self.command_execute_status.remove()
                except Exception as e:
                    self.logger.error(f"Error removing command_execute_status: {e}")
                # 属性を削除
                delattr(self, "command_execute_status")
            
            # new_wish_main_paneとnew_wish_sub_paneの子ウィジェットをチェックして、フォームをアンマウント
            try:
                # Main Paneのフォームをアンマウント
                children = list(self.new_wish_main_pane._nodes)
                for child in children:
                    # main-pane-content以外のウィジェットをアンマウント
                    if child.id != "main-pane-content" and (child.id.endswith("-form") or child.id.endswith("-status")):
                        self.logger.debug(f"Removing widget with ID: {child.id} from Main Pane")
                        try:
                            child.remove()
                        except Exception as e:
                            self.logger.error(f"Error removing child widget {child.id} from Main Pane: {e}")
                
                # Sub Paneのフォームをアンマウント
                children = list(self.new_wish_sub_pane._nodes)
                for child in children:
                    # sub-pane-content以外のウィジェットをアンマウント
                    if child.id != "sub-pane-content" and (child.id.endswith("-form") or child.id.endswith("-status")):
                        self.logger.debug(f"Removing widget with ID: {child.id} from Sub Pane")
                        try:
                            child.remove()
                        except Exception as e:
                            self.logger.error(f"Error removing child widget {child.id} from Sub Pane: {e}")
            except Exception as e:
                self.logger.error(f"Error processing pane children: {e}")
        except Exception as e:
            self.logger.error(f"Error in _unmount_new_wish_forms: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
    
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
            # 入力を処理
            self.new_wish_composite.handle_wish_input(event.wish_text)
            
            # UIを更新
            self.update_new_wish_ui()
        except Exception as e:
            self.logger.error(f"Error handling WishInputSubmitted: {e}")
    
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
        self.new_wish_composite.handle_execution_confirmed(app=self.app)
        self.update_new_wish_ui()
    
    def on_execution_cancelled(self, event: ExecutionCancelled) -> None:
        """Handle execution cancelled message."""
        self.new_wish_composite.handle_execution_cancelled()
        self.update_new_wish_ui()
    
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
