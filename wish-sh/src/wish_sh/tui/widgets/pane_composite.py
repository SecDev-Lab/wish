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
            self.main_pane.update_for_suggest_commands(commands)
            self.sub_pane.update_for_suggest_commands()
            
        elif current_state == NewWishState.ADJUST_COMMANDS:
            commands = self.new_wish_turns.get_current_commands()
            self.main_pane.update_for_adjust_commands(commands)
            self.sub_pane.update_for_adjust_commands()
            
        elif current_state == NewWishState.CONFIRM_COMMANDS:
            commands = self.new_wish_turns.get_selected_commands() or self.new_wish_turns.get_current_commands()
            self.main_pane.update_for_confirm_commands(commands)
            self.sub_pane.update_for_confirm_commands()
            
        elif current_state == NewWishState.EXECUTE_COMMANDS:
            commands = self.new_wish_turns.get_selected_commands() or self.new_wish_turns.get_current_commands()
            self.main_pane.update_for_execute_commands(commands)
            self.sub_pane.update_for_execute_commands()
    
    def handle_wish_input(self, wish_text: str) -> None:
        """Handle wish input.
        
        Args:
            wish_text: The wish text.
        """
        # Wishの内容を分析
        if self.is_wish_sufficient(wish_text):
            # 十分な情報があればコマンド提案へ
            from wish_models import Wish
            wish = Wish.create(wish_text)
            self.new_wish_turns.set_current_wish(wish)
            
            # コマンドを生成
            from wish_sh.wish_manager import WishManager
            from wish_sh.settings import Settings
            manager = WishManager(Settings())
            commands = manager.generate_commands(wish_text)
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
        self.update_for_state()
    
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
    
    def handle_wish_detail(self, detail: str) -> None:
        """Handle wish detail.
        
        Args:
            detail: The wish detail.
        """
        self.new_wish_turns.set_wish_detail(detail)
        
        # 現在のWishとコマンドを取得
        wish = self.new_wish_turns.get_current_wish()
        if wish:
            # Wishを更新
            wish.wish = f"{wish.wish} on {detail}"
            self.new_wish_turns.set_current_wish(wish)
            
            # コマンドを更新
            from wish_sh.wish_manager import WishManager
            from wish_sh.settings import Settings
            manager = WishManager(Settings())
            commands = manager.generate_commands(wish.wish)
            self.new_wish_turns.set_current_commands(commands)
        
        # 状態遷移
        self.new_wish_turns.transition(NewWishEvent.DETAIL_PROVIDED)
        
        # UI更新
        self.update_for_state()
    
    def handle_commands_accepted(self) -> None:
        """Handle commands accepted."""
        # 状態遷移
        self.new_wish_turns.transition(NewWishEvent.COMMANDS_ACCEPTED)
        
        # UI更新
        self.update_for_state()
    
    def handle_commands_rejected(self) -> None:
        """Handle commands rejected."""
        # 状態遷移
        self.new_wish_turns.transition(NewWishEvent.COMMANDS_REJECTED)
        
        # UI更新
        self.update_for_state()
    
    def handle_command_adjust_requested(self) -> None:
        """Handle command adjust requested."""
        # 状態遷移
        self.new_wish_turns.transition(NewWishEvent.ADJUSTMENT_REQUESTED)
        
        # UI更新
        self.update_for_state()
    
    def handle_commands_adjusted(self, commands: List[str]) -> None:
        """Handle commands adjusted.
        
        Args:
            commands: The adjusted commands.
        """
        # 調整されたコマンドを設定
        self.new_wish_turns.set_selected_commands(commands)
        
        # 状態遷移
        self.new_wish_turns.transition(NewWishEvent.COMMANDS_ADJUSTED)
        
        # UI更新
        self.update_for_state()
    
    def handle_command_adjust_cancelled(self) -> None:
        """Handle command adjust cancelled."""
        # 状態遷移
        self.new_wish_turns.transition(NewWishEvent.BACK_TO_INPUT)
        
        # UI更新
        self.update_for_state()
    
    def handle_execution_confirmed(self) -> None:
        """Handle execution confirmed."""
        # 状態遷移
        self.new_wish_turns.transition(NewWishEvent.EXECUTION_CONFIRMED)
        
        # コマンドを実行
        wish = self.new_wish_turns.get_current_wish()
        commands = self.new_wish_turns.get_selected_commands() or self.new_wish_turns.get_current_commands()
        
        if wish and commands:
            # コマンドを実行
            from wish_sh.wish_manager import WishManager
            from wish_sh.settings import Settings
            manager = WishManager(Settings())
            for cmd_num, cmd in enumerate(commands, start=1):
                manager.execute_command(wish, cmd, cmd_num)
            
            # Wishを保存
            manager.current_wish = wish
            manager.save_wish(wish)
        
        # UI更新
        self.update_for_state()
    
    def handle_execution_cancelled(self) -> None:
        """Handle execution cancelled."""
        # 状態遷移
        self.new_wish_turns.transition(NewWishEvent.EXECUTION_CANCELLED)
        
        # UI更新
        self.update_for_state()
