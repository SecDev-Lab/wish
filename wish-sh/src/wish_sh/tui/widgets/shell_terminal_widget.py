"""Shell Terminal Widget for wish-sh TUI."""

from typing import List, Optional
import string
import asyncio

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static, RichLog, Input
from textual.reactive import reactive
from textual.timer import Timer

from wish_sh.tui.new_wish_messages import WishInputSubmitted
from wish_sh.logging import setup_logger


class ShellTerminalWidget(Static):
    """A terminal-like widget that emulates a shell experience."""
    
    # キーイベントを直接キャプチャするためのフラグ
    can_focus = True
    
    # 入力処理中フラグ
    _processing_input = False
    
    def __init__(self, prompt: str = "wish✨️ ", *args, **kwargs):
        """Initialize the widget.
        
        Args:
            prompt: The prompt to display before input.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(*args, **kwargs)
        self.prompt = prompt
        self.command_history: List[str] = []
        self.command_history_index = -1
        self.logger = setup_logger("wish_sh.tui.ShellTerminalWidget")
        
        # 現在の入力テキストを管理
        self.current_input = ""
        # カーソル位置（文字インデックス）
        self.cursor_position = 0
        # カーソルの表示状態（点滅用）
        self.cursor_visible = True
        # カーソル点滅用タイマー
        self.cursor_timer: Optional[Timer] = None
    
    def compose(self) -> ComposeResult:
        """Compose the widget."""
        # 出力表示用のRichLogウィジェット
        yield RichLog(id="terminal-output", wrap=False, highlight=True, markup=False)
        # 非表示の入力フィールド（キーイベントのバックアップ用）
        yield Input(id="hidden-input", classes="hidden")
    
    def on_mount(self) -> None:
        """Event handler called when the widget is mounted."""
        # 出力領域への参照を取得
        self.output = self.query_one("#terminal-output", RichLog)
        # 非表示入力フィールドへの参照を取得
        self.hidden_input = self.query_one("#hidden-input", Input)
        
        # ウィジェットにフォーカスを設定
        self.focus()
        
        # カーソル点滅用タイマーを設定（500ms間隔）
        self.cursor_timer = self.set_interval(0.5, self.blink_cursor)
        
        # 初期プロンプトを表示
        self.update_prompt_line()
    
    def blink_cursor(self) -> None:
        """カーソルを点滅させる"""
        self.cursor_visible = not self.cursor_visible
        # カーソルの点滅時は、プロンプトラインの更新のみを行う（出力は行わない）
        self.update_cursor_only()
    
    def update_cursor_only(self) -> None:
        """カーソルの表示状態のみを更新する"""
        # 現在の入力行を構築
        if self.cursor_visible:
            # カーソル位置に可視カーソルを挿入
            cursor_char = "█"
            if self.cursor_position < len(self.current_input):
                # カーソルが入力テキストの途中にある場合
                input_with_cursor = (
                    self.current_input[:self.cursor_position] + 
                    cursor_char + 
                    self.current_input[self.cursor_position:]
                )
            else:
                # カーソルが入力テキストの最後にある場合
                input_with_cursor = self.current_input + cursor_char
        else:
            # カーソルが非表示の場合、カーソル位置にスペースを挿入
            if self.cursor_position < len(self.current_input):
                input_with_cursor = (
                    self.current_input[:self.cursor_position] + 
                    " " + 
                    self.current_input[self.cursor_position:]
                )
            else:
                input_with_cursor = self.current_input + " "
        
        # 最後の行を更新（プロンプトと入力テキスト）
        self.output.refresh()
        lines = self.output.lines
        
        # 出力をクリア
        self.output.clear()
        
        # 最後の行がある場合のみ処理
        if lines and len(lines) > 1:
            # 現在の内容を保存（最後の行以外）
            for i in range(len(lines) - 1):
                line_text = ""
                for segment in lines[i].segments:
                    line_text += segment.text
                # 保存した行を再度追加
                self.output.write(line_text)
        
        # 新しいプロンプトラインを追加
        self.output.write(f"{self.prompt}{input_with_cursor}")
        
        # 自動スクロール
        self.output.scroll_end()
    
    def update_prompt_line(self) -> None:
        """プロンプトラインを更新する"""
        # 現在の入力行を構築
        if self.cursor_visible:
            # カーソル位置に可視カーソルを挿入
            cursor_char = "█"
            if self.cursor_position < len(self.current_input):
                # カーソルが入力テキストの途中にある場合
                input_with_cursor = (
                    self.current_input[:self.cursor_position] + 
                    cursor_char + 
                    self.current_input[self.cursor_position:]
                )
            else:
                # カーソルが入力テキストの最後にある場合
                input_with_cursor = self.current_input + cursor_char
        else:
            # カーソルが非表示の場合、カーソル位置にスペースを挿入
            if self.cursor_position < len(self.current_input):
                input_with_cursor = (
                    self.current_input[:self.cursor_position] + 
                    " " + 
                    self.current_input[self.cursor_position:]
                )
            else:
                input_with_cursor = self.current_input + " "
        
        # 最後の行を更新（プロンプトと入力テキスト）
        self.output.refresh()
        lines = self.output.lines
        
        # 出力をクリア
        self.output.clear()
        
        # 最後の行がある場合のみ処理
        if lines and len(lines) > 1:
            # 現在の内容を保存（最後の行以外）
            for i in range(len(lines) - 1):
                line_text = ""
                for segment in lines[i].segments:
                    line_text += segment.text
                # 保存した行を再度追加
                self.output.write(line_text)
        
        # 新しいプロンプトラインを追加
        self.output.write(f"{self.prompt}{input_with_cursor}")
        
        # 自動スクロール
        self.output.scroll_end()
    
    def submit_current_input(self) -> None:
        """現在の入力を送信する"""
        # 処理中フラグを設定
        if self._processing_input:
            self.logger.debug("Already processing input, ignoring")
            return
        
        self._processing_input = True
        
        try:
            command = self.current_input
            
            self.logger.debug(f"Attempting to submit input: '{command}'")
            
            if not command.strip():
                # 空の入力は送信しない
                self.logger.debug("Empty input, not submitting")
                self._processing_input = False
                return
            
            # 入力行を確定（カーソルなしで表示）
            self.output.refresh()
            lines = self.output.lines
            
            # 出力をクリア
            self.output.clear()
            
            # 最後の行がある場合のみ処理
            if lines and len(lines) > 1:
                # 現在の内容を保存（最後の行以外）
                for i in range(len(lines) - 1):
                    line_text = ""
                    for segment in lines[i].segments:
                        line_text += segment.text
                    # 保存した行を再度追加
                    self.output.write(line_text)
            
            # 確定した入力を表示
            self.output.write(f"{self.prompt}{command}")
            
            # コマンド履歴に追加
            if command not in self.command_history:
                self.command_history.append(command)
            self.command_history_index = -1
            
            # 入力をクリア
            old_input = self.current_input
            self.current_input = ""
            self.cursor_position = 0
            
            # 新しいプロンプトラインを表示
            self.update_prompt_line()
            
            # 入力メッセージを送信
            self.logger.debug(f"Creating WishInputSubmitted message for command: '{old_input}'")
            message = WishInputSubmitted(old_input)
            
            # メッセージを直接送信
            self.logger.debug(f"Posting message: {message}")
            try:
                self.logger.debug("DEBUGGING: About to post WishInputSubmitted message")
                self.logger.debug(f"DEBUGGING: Message content: {message.wish_text}")
                self.logger.debug(f"DEBUGGING: Message type: {type(message)}")
                self.logger.debug(f"DEBUGGING: Current widget: {self}")
                self.logger.debug(f"DEBUGGING: Parent widget: {self.parent}")
                
                # メッセージを送信
                self.post_message(message)
                
                self.logger.debug("DEBUGGING: WishInputSubmitted message posted successfully")
                self.logger.debug(f"DEBUGGING: Message successfully posted from {self} to parent")
            except Exception as e:
                self.logger.error(f"DEBUGGING: Error posting message: {e}")
                import traceback
                self.logger.error(f"DEBUGGING: Traceback: {traceback.format_exc()}")
            
            self.logger.debug(f"Input submitted successfully: '{old_input}'")
        except Exception as e:
            self.logger.error(f"Error in submit_current_input: {e}")
        finally:
            # 処理中フラグをリセット
            self._processing_input = False
    
    def on_key(self, event) -> None:
        """キーイベントを処理する（キーが押された時）"""
        # 必ずフォーカスを確保
        self.focus()
        
        key = event.key
        
        # エンターキーで入力を送信
        if key == "enter":
            self.submit_current_input()
            event.prevent_default()
            event.stop()
            return
        
        # バックスペースで文字を削除
        elif key == "backspace":
            if self.cursor_position > 0:
                self.current_input = (
                    self.current_input[:self.cursor_position-1] + 
                    self.current_input[self.cursor_position:]
                )
                self.cursor_position -= 1
                self.update_prompt_line()
            event.prevent_default()
            event.stop()
            return
        
        # 削除キーで文字を削除
        elif key == "delete":
            if self.cursor_position < len(self.current_input):
                self.current_input = (
                    self.current_input[:self.cursor_position] + 
                    self.current_input[self.cursor_position+1:]
                )
                self.update_prompt_line()
            event.prevent_default()
            event.stop()
            return
        
        # 左矢印でカーソルを左に移動
        elif key == "left":
            if self.cursor_position > 0:
                self.cursor_position -= 1
                self.update_prompt_line()
            event.prevent_default()
            event.stop()
            return
        
        # 右矢印でカーソルを右に移動
        elif key == "right":
            if self.cursor_position < len(self.current_input):
                self.cursor_position += 1
                self.update_prompt_line()
            event.prevent_default()
            event.stop()
            return
        
        # ホームキーでカーソルを行頭に移動
        elif key == "home":
            self.cursor_position = 0
            self.update_prompt_line()
            event.prevent_default()
            event.stop()
            return
        
        # エンドキーでカーソルを行末に移動
        elif key == "end":
            self.cursor_position = len(self.current_input)
            self.update_prompt_line()
            event.prevent_default()
            event.stop()
            return
        
        # 上矢印でコマンド履歴を遡る
        elif key == "up":
            if self.command_history and self.command_history_index < len(self.command_history) - 1:
                if self.command_history_index == -1:
                    # 履歴ナビゲーションを開始する場合、現在の入力を保存
                    self.saved_input = self.current_input
                
                self.command_history_index += 1
                self.current_input = self.command_history[-(self.command_history_index + 1)]
                self.cursor_position = len(self.current_input)
                self.update_prompt_line()
            event.prevent_default()
            event.stop()
            return
        
        # 下矢印でコマンド履歴を進む
        elif key == "down":
            if self.command_history_index > -1:
                self.command_history_index -= 1
                if self.command_history_index == -1:
                    # 履歴の最後に達した場合、保存した入力を復元
                    self.current_input = getattr(self, 'saved_input', '')
                else:
                    self.current_input = self.command_history[-(self.command_history_index + 1)]
                self.cursor_position = len(self.current_input)
                self.update_prompt_line()
            event.prevent_default()
            event.stop()
            return
        
        # 通常の文字入力
        if len(key) == 1 and (key in string.printable):
            # カーソル位置に文字を挿入
            self.current_input = (
                self.current_input[:self.cursor_position] + 
                key + 
                self.current_input[self.cursor_position:]
            )
            self.cursor_position += 1
            self.update_prompt_line()
            event.prevent_default()
            event.stop()
    
    def on_key_up(self, event) -> None:
        """キーイベントを処理する（キーが離された時）"""
        # 必ずフォーカスを確保
        self.focus()
        
        # 全てのキーイベントを消費
        event.prevent_default()
        event.stop()
    
    def add_output(self, output: str) -> None:
        """出力テキストをターミナルに追加する
        
        Args:
            output: 追加する出力テキスト
        """
        if output:
            # 現在のプロンプトラインを一時的に削除
            self.output.refresh()
            lines = self.output.lines
            
            # 出力をクリア
            self.output.clear()
            
            # 最後の行がある場合のみ処理
            if lines and len(lines) > 1:
                # 現在の内容を保存（最後の行以外）
                for i in range(len(lines) - 1):
                    line_text = ""
                    for segment in lines[i].segments:
                        line_text += segment.text
                    # 保存した行を再度追加
                    self.output.write(line_text)
            
            # 出力をRichLogに追加
            for line in output.rstrip().split("\n"):
                self.output.write(line)
            
            # プロンプトラインを再表示
            self.update_prompt_line()
    
    def clear_terminal(self) -> None:
        """ターミナル履歴をクリアする"""
        self.output.clear()
        # プロンプトラインを再表示
        self.update_prompt_line()
