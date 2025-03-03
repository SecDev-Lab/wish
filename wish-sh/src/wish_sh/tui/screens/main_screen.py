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
from wish_sh.tui.widgets.main_pane import MainPane, CommandSelected
from wish_sh.tui.widgets.sub_pane import SubPane
from wish_sh.tui.widgets.wish_select_pane import WishSelectPane, WishSelected


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
        self.main_pane = MainPane(id="main-pane")
        self.sub_pane = SubPane(id="sub-pane")
        self.help_pane = HelpPane(id="help-pane")

        # Yield the widgets in the desired order
        yield self.wish_select
        yield self.main_pane
        yield self.sub_pane
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
        # Set initial focus to the main pane
        self.main_pane.focus()
        
        # Set initial active state
        self.wish_select.set_active(False)
        self.main_pane.set_active(True)
        self.sub_pane.set_active(False)
        
        # Update help text for initial active pane
        self.help_pane.update_help("main-pane")
        
        # Initialize with NEW_WISH mode
        self.set_mode(WishMode.NEW_WISH)
    
    def on_key(self, event) -> None:
        """Handle key events."""
        # Log key events at debug level
        self.logger.debug(f"Key event: {event.key}")
        self.logger.debug(f"Active pane: wish_select={self.wish_select.has_class('active-pane')}, "
                         f"main_pane={self.main_pane.has_class('active-pane')}, "
                         f"sub_pane={self.sub_pane.has_class('active-pane')}")
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
        
        # Handle up/down keys when Main pane is active and in WISH_HISTORY mode
        if self.main_pane.has_class("active-pane") and self.current_mode == WishMode.WISH_HISTORY:
            if event.key in ("up", "arrow_up", "down", "arrow_down"):
                self.logger.debug("Passing up/down key to main_pane")
                # Pass the key event to the main pane
                if self.main_pane.on_key(event):
                    return True  # Consume event if the main pane handled it
                else:
                    self.logger.debug("main_pane did not handle the key event")
        
        # Handle o/e keys when Sub pane is active and in WISH_HISTORY mode
        if self.sub_pane.has_class("active-pane") and self.current_mode == WishMode.WISH_HISTORY:
            if event.key in ("o", "e"):
                self.logger.debug(f"Passing {event.key} key to sub_pane")
                # Pass the key event to the sub pane
                if self.sub_pane.on_key(event):
                    return True  # Consume event if the sub pane handled it
                else:
                    self.logger.debug(f"sub_pane did not handle the {event.key} key event")
        
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
        self.main_pane.set_active(False)
        self.sub_pane.set_active(False)
        
        # Activate the specified pane
        if pane_id == "wish-select":
            self.wish_select.set_active(True)
            self.wish_select.focus()
        elif pane_id == "main-pane":
            self.main_pane.set_active(True)
            self.main_pane.focus()
        elif pane_id == "sub-pane":
            self.sub_pane.set_active(True)
            self.sub_pane.focus()
        
        # Update help text based on active pane
        self.help_pane.update_help(pane_id)
    
    def display_command(self, command_result):
        """Display command details in the sub pane.
        
        Args:
            command_result: The command result to display.
        """
        if command_result:
            self.sub_pane.update_command_output(command_result)
    
    def set_mode(self, mode: WishMode, wish=None) -> None:
        """Set the current mode and update panes accordingly.
        
        Args:
            mode: The mode to set.
            wish: The wish to display (for WISH_HISTORY mode).
        """
        self.current_mode = mode
        
        if mode == WishMode.NEW_WISH:
            # Update panes for NEW WISH mode
            self.main_pane.update_for_new_wish_mode()
            self.sub_pane.update_for_new_wish_mode()
            
            # Reset NewWishTurns to initial state
            self.new_wish_turns.current_state = NewWishState.INPUT_WISH
            self.update_new_wish_ui()
        else:
            # Update panes for WISH HISTORY mode
            self.main_pane.update_wish(wish)
            
            # wishにコマンドがある場合、最初のコマンドを表示
            if wish and wish.command_results:
                self.display_command(wish.command_results[0])
            else:
                # コマンドがない場合は従来通りのメッセージを表示
                content_widget = self.sub_pane.query_one("#sub-pane-content")
                content_widget.update(self.sub_pane.MSG_NO_COMMAND_SELECTED)
    
    def update_new_wish_ui(self) -> None:
        """Update UI based on current NewWishState."""
        current_state = self.new_wish_turns.current_state
        
        # Import New Wish widgets
        from wish_sh.tui.widgets.new_wish_widgets import (
            WishInputForm,
            WishDetailForm,
            CommandSuggestForm,
            CommandAdjustForm,
            CommandConfirmForm,
            CommandExecuteStatus,
        )
        
        # 現在のフォームをアンマウント
        self._unmount_new_wish_forms()
        
        # 現在の状態に応じてUIを更新
        if current_state == NewWishState.INPUT_WISH:
            self.main_pane.update_for_input_wish()
            self.sub_pane.update_for_input_wish()
            
            # WishInputFormをマウント
            self.wish_input_form = WishInputForm(id="wish-input-form")
            self.main_pane.mount(self.wish_input_form)
            
        elif current_state == NewWishState.ASK_WISH_DETAIL:
            self.main_pane.update_for_ask_wish_detail()
            self.sub_pane.update_for_ask_wish_detail()
            
            # WishDetailFormをマウント
            self.wish_detail_form = WishDetailForm(id="wish-detail-form")
            self.main_pane.mount(self.wish_detail_form)
            
        elif current_state == NewWishState.SUGGEST_COMMANDS:
            commands = self.new_wish_turns.get_current_commands()
            self.main_pane.update_for_suggest_commands(commands)
            self.sub_pane.update_for_suggest_commands()
            
            # CommandSuggestFormをマウント
            self.command_suggest_form = CommandSuggestForm(commands, id="command-suggest-form")
            self.main_pane.mount(self.command_suggest_form)
            
        elif current_state == NewWishState.ADJUST_COMMANDS:
            commands = self.new_wish_turns.get_current_commands()
            self.main_pane.update_for_adjust_commands(commands)
            self.sub_pane.update_for_adjust_commands()
            
            # CommandAdjustFormをマウント
            self.command_adjust_form = CommandAdjustForm(commands, id="command-adjust-form")
            self.main_pane.mount(self.command_adjust_form)
            
        elif current_state == NewWishState.CONFIRM_COMMANDS:
            commands = self.new_wish_turns.get_selected_commands() or self.new_wish_turns.get_current_commands()
            self.main_pane.update_for_confirm_commands(commands)
            self.sub_pane.update_for_confirm_commands()
            
            # CommandConfirmFormをマウント
            self.command_confirm_form = CommandConfirmForm(commands, id="command-confirm-form")
            self.main_pane.mount(self.command_confirm_form)
            
        elif current_state == NewWishState.EXECUTE_COMMANDS:
            commands = self.new_wish_turns.get_selected_commands() or self.new_wish_turns.get_current_commands()
            self.main_pane.update_for_execute_commands(commands)
            self.sub_pane.update_for_execute_commands()
            
            # 一意のIDを生成するために現在時刻のタイムスタンプを使用
            import time
            unique_id = f"command-execute-status-{int(time.time())}"
            self.logger.debug(f"Creating CommandExecuteStatus with unique ID: {unique_id}")
            
            # CommandExecuteStatusをマウント
            self.command_execute_status = CommandExecuteStatus(commands, id=unique_id)
            self.main_pane.mount(self.command_execute_status)
    
    def _unmount_new_wish_forms(self) -> None:
        """Unmount all New Wish forms."""
        # 直接main_paneの子ウィジェットをチェックして、フォームをアンマウント
        try:
            # main_paneの子ウィジェットをコピーして反復処理
            children = list(self.main_pane._nodes)
            for child in children:
                # main-pane-content以外のウィジェットをアンマウント
                if child.id != "main-pane-content":
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
        # Do not activate the sub pane to keep focus on main pane
        # self.activate_pane("sub-pane")
        
    def on_activate_pane(self, event: ActivatePane) -> None:
        """Handle pane activation requests."""
        self.activate_pane(event.pane_id)
    
    # New Wish mode message handlers
    def on_wish_input_submitted(self, event: WishInputSubmitted) -> None:
        """Handle WishInputSubmitted message."""
        wish_text = event.wish_text
        
        # Wishの内容を分析
        if self.is_wish_sufficient(wish_text):
            # 十分な情報があればコマンド提案へ
            from wish_models import Wish
            wish = Wish.create(wish_text)
            self.new_wish_turns.set_current_wish(wish)
            
            # コマンドを生成
            commands = self.manager.generate_commands(wish_text)
            self.new_wish_turns.set_current_commands(commands)
            
            # 状態遷移
            self.new_wish_turns.transition(NewWishEvent.SUFFICIENT_WISH)
        else:
            # 不十分な情報ならば詳細入力へ
            from wish_models import Wish
            wish = Wish.create(wish_text)
            self.new_wish_turns.set_current_wish(wish)
            
            # 状態遷移
            self.new_wish_turns.transition(NewWishEvent.INSUFFICIENT_WISH)
        
        # UI更新
        self.update_new_wish_ui()
    
    def is_wish_sufficient(self, wish_text: str) -> bool:
        """Wishに十分な情報があるかを判定する。
        
        Args:
            wish_text: Wishのテキスト
            
        Returns:
            bool: 十分な情報があるかどうか
        """
        # 実際の実装では、より複雑な判定ロジックが必要
        if "scan" in wish_text.lower() and "port" in wish_text.lower():
            # ポートスキャンの場合、ターゲットIPが必要
            return "10.10.10" in wish_text or "192.168" in wish_text
        return True
    
    def on_wish_detail_submitted(self, event: WishDetailSubmitted) -> None:
        """Handle WishDetailSubmitted message."""
        detail = event.detail
        self.new_wish_turns.set_wish_detail(detail)
        
        # 現在のWishとコマンドを取得
        wish = self.new_wish_turns.get_current_wish()
        if wish:
            # Wishを更新
            wish.wish = f"{wish.wish} on {detail}"
            self.new_wish_turns.set_current_wish(wish)
            
            # コマンドを更新
            commands = self.manager.generate_commands(wish.wish)
            self.new_wish_turns.set_current_commands(commands)
        
        # 状態遷移
        self.new_wish_turns.transition(NewWishEvent.DETAIL_PROVIDED)
        
        # UI更新
        self.update_new_wish_ui()
    
    def on_commands_accepted(self, event: CommandsAccepted) -> None:
        """Handle CommandsAccepted message."""
        # 状態遷移
        self.new_wish_turns.transition(NewWishEvent.COMMANDS_ACCEPTED)
        
        # UI更新
        self.update_new_wish_ui()
    
    def on_commands_rejected(self, event: CommandsRejected) -> None:
        """Handle CommandsRejected message."""
        # 状態遷移
        self.new_wish_turns.transition(NewWishEvent.COMMANDS_REJECTED)
        
        # UI更新
        self.update_new_wish_ui()
    
    def on_command_adjust_requested(self, event: CommandAdjustRequested) -> None:
        """Handle CommandAdjustRequested message."""
        # 状態遷移
        self.new_wish_turns.transition(NewWishEvent.ADJUSTMENT_REQUESTED)
        
        # UI更新
        self.update_new_wish_ui()
    
    def on_commands_adjusted(self, event: CommandsAdjusted) -> None:
        """Handle CommandsAdjusted message."""
        # 調整されたコマンドを設定
        self.new_wish_turns.set_selected_commands(event.commands)
        
        # 状態遷移
        self.new_wish_turns.transition(NewWishEvent.COMMANDS_ADJUSTED)
        
        # UI更新
        self.update_new_wish_ui()
    
    def on_command_adjust_cancelled(self, event: CommandAdjustCancelled) -> None:
        """Handle CommandAdjustCancelled message."""
        # 状態遷移
        self.new_wish_turns.transition(NewWishEvent.BACK_TO_INPUT)
        
        # UI更新
        self.update_new_wish_ui()
    
    def on_execution_confirmed(self, event: ExecutionConfirmed) -> None:
        """Handle ExecutionConfirmed message."""
        # 状態遷移
        self.new_wish_turns.transition(NewWishEvent.EXECUTION_CONFIRMED)
        
        # コマンドを実行
        wish = self.new_wish_turns.get_current_wish()
        commands = self.new_wish_turns.get_selected_commands() or self.new_wish_turns.get_current_commands()
        
        if wish and commands:
            # コマンドを実行
            for cmd_num, cmd in enumerate(commands, start=1):
                self.manager.execute_command(wish, cmd, cmd_num)
            
            # Wishを保存
            self.manager.current_wish = wish
            self.manager.save_wish(wish)
        
        # UI更新
        self.update_new_wish_ui()
    
    def on_execution_cancelled(self, event: ExecutionCancelled) -> None:
        """Handle ExecutionCancelled message."""
        # 状態遷移
        self.new_wish_turns.transition(NewWishEvent.EXECUTION_CANCELLED)
        
        # UI更新
        self.update_new_wish_ui()
