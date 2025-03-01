"""Main Pane widget for wish-sh TUI."""

from datetime import datetime
from textual.app import ComposeResult
from textual.message import Message
from textual.widgets import Static
from textual.containers import Horizontal
from rich.markup import escape

from wish_models import CommandState, CommandResult, WishState, UtcDatetime
from wish_sh.tui.widgets.base_pane import BasePane


class CommandSelected(Message):
    """Message sent when a command is selected."""

    def __init__(self, command_result: CommandResult):
        """Initialize the message.
        
        Args:
            command_result: The selected command result.
        """
        self.command_result = command_result
        super().__init__()


class MainPane(BasePane):
    """Main content pane."""

    # CSS moved to external file: wish_tui.css

    def __init__(self, *args, **kwargs):
        """Initialize the MainPane.
        
        Args:
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(*args, **kwargs)
        self.current_wish = None
        self.selected_command_index = -1  # -1 means no command selected

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        yield Static("(Main content will be displayed here)", id="main-pane-content", markup=True)
    
    def update_for_new_wish_mode(self):
        """Update the pane for New Wish mode."""
        # Remove old grid if exists
        try:
            old_grid = self.query_one("#wish-details-grid")
            self.remove(old_grid)
        except:
            pass
            
        content_widget = self.query_one("#main-pane-content")
        content_widget.update("[b]新しいWishを作成するモードです。[/b]")
    
    def _get_wish_state_emoji(self, state):
        """Get emoji for wish state."""
        if state == WishState.DOING:
            return "🔄"
        elif state == WishState.DONE:
            return "✅"
        elif state == WishState.FAILED:
            return "❌"
        elif state == WishState.CANCELLED:
            return "🚫"
        else:
            return "❓"

    def _get_command_state_emoji(self, state):
        """Get emoji for command state."""
        if state == CommandState.DOING:
            return "🔄"
        elif state == CommandState.SUCCESS:
            return "✅"
        elif state == CommandState.USER_CANCELLED:
            return "🚫"
        elif state == CommandState.COMMAND_NOT_FOUND:
            return "🔍❌"
        elif state == CommandState.FILE_NOT_FOUND:
            return "📄❌"
        elif state == CommandState.REMOTE_OPERATION_FAILED:
            return "🌐❌"
        elif state == CommandState.TIMEOUT:
            return "⏱️"
        elif state == CommandState.NETWORK_ERROR:
            return "📡❌"
        elif state == CommandState.OTHERS:
            return "❌"
        else:
            return "❓"
    
    def update_wish(self, wish, preserve_selection=False):
        """Update the pane with the selected wish details.
        
        Args:
            wish: The wish to display.
            preserve_selection: Whether to preserve the current selection.
        """
        try:
            # Wishが変わったかどうかをチェック
            wish_changed = self.current_wish != wish
            self.current_wish = wish
            
            # Wishが変わった場合のみ選択をリセット
            if wish_changed and not preserve_selection:
                self.log(f"Resetting selection because wish changed and preserve_selection={preserve_selection}")
                self.selected_command_index = -1  # Default to no selection
                
                # If wish has commands, select the first one (index 0)
                if wish and wish.command_results and len(wish.command_results) > 0:
                    self.selected_command_index = 0
            
            self.log(f"update_wish: selected_command_index={self.selected_command_index}, preserve_selection={preserve_selection}")
            
            # Get existing content widget
            try:
                content = self.query_one("#main-pane-content")
            except:
                # Create a new content widget if it doesn't exist
                content = Static(id="main-pane-content")
                self.mount(content)
            
            if wish:
                # Get emoji for wish state
                state_emoji = self._get_wish_state_emoji(wish.state)
                
                # Convert UTC times to local time
                if isinstance(wish.created_at, str):
                    # Convert string to UtcDatetime
                    created_at_dt = UtcDatetime.model_validate(wish.created_at)
                    created_at_local = created_at_dt.to_local_str()
                else:
                    created_at_local = wish.created_at.to_local_str()
                
                finished_at_text = "(Not finished yet)"
                if wish.finished_at:
                    if isinstance(wish.finished_at, str):
                        # Convert string to UtcDatetime
                        finished_at_dt = UtcDatetime.model_validate(wish.finished_at)
                        finished_at_text = finished_at_dt.to_local_str()
                    else:
                        finished_at_text = wish.finished_at.to_local_str()
                
                # Create two separate widgets: one for labels (with markup) and one for values (without markup)
                # Format wish details as text
                label_lines = []
                value_lines = []
                
                # Add wish details - with label and value separated
                label_lines.append("[b]Wish:[/b]")
                value_lines.append(wish.wish)
                
                label_lines.append(f"[b]Status:[/b]")
                value_lines.append(f"{state_emoji} {wish.state}")
                
                label_lines.append(f"[b]Created:[/b]")
                value_lines.append(created_at_local)
                
                label_lines.append(f"[b]Finished:[/b]")
                value_lines.append(finished_at_text)
                
                label_lines.append("")
                value_lines.append("")
                
                label_lines.append("[b]Commands:[/b]")
                value_lines.append("")
                
                # Add command results
                for i, cmd in enumerate(wish.command_results, 1):
                    cmd_emoji = self._get_command_state_emoji(cmd.state)
                    label_lines.append(f"{cmd_emoji} ({i})")
                    value_lines.append(cmd.command)
                
                # Remove old grid if exists (but keep the content widget)
                try:
                    old_grid = self.query_one("#wish-details-grid")
                    self.remove(old_grid)
                except:
                    pass
                
                # Create content lines for the widget
                content_lines = []
                
                # Add wish details with label and value on the same line
                content_lines.append(f"[b]Wish:[/b]     {escape(wish.wish)}")
                content_lines.append(f"[b]Status:[/b]   {state_emoji} {wish.state}")
                content_lines.append(f"[b]Created:[/b]  {created_at_local}")
                content_lines.append(f"[b]Finished:[/b] {finished_at_text}")
                content_lines.append("")
                content_lines.append("[b]Commands:[/b]")
                
                # Add command results
                for i, cmd in enumerate(wish.command_results, 1):
                    cmd_emoji = self._get_command_state_emoji(cmd.state)
                    # Use rich.markup.escape to escape any markup in the command text
                    escaped_command = escape(cmd.command)
                    content_lines.append(f"{cmd_emoji} ({i}) {escaped_command}")
                
                # Create a simple content widget with both label and value - NO MARKUP
                content_lines = []
                
                # Add wish details with label and value on the same line
                content_lines.append(f"Wish:     {wish.wish}")
                content_lines.append(f"Status:   {state_emoji} {wish.state}")
                content_lines.append(f"Created:  {created_at_local}")
                content_lines.append(f"Finished: {finished_at_text}")
                content_lines.append("")
                content_lines.append("Commands:")
                
                # Add command results
                self.command_indices = []  # Store command indices for click handling
                for i, cmd in enumerate(wish.command_results, 1):
                    cmd_emoji = self._get_command_state_emoji(cmd.state)
                    
                    # TODO: この文字置換による対応は暫定的な回避策です。
                    # 問題点:
                    # 1. テキストの内容を変更してしまうため、本来の情報が正確に表示されない
                    # 2. 将来的に問題を引き起こす可能性のある他の特殊文字が出てくる可能性がある
                    # 3. より根本的な解決策としては、Textualのウィジェットの実装を見直すか、
                    #    マークアップ処理を完全に無効化する方法を探るべき
                    #
                    # 適切な解決策:
                    # - Textualの新しいバージョンでマークアップ処理が改善されるか確認する
                    # - カスタムウィジェットを作成して、マークアップ処理を完全に制御する
                    # - 表示用と内部処理用のテキストを分離し、表示用テキストのみを安全に加工する
                    
                    # Replace problematic characters in command text
                    safe_command = cmd.command
                    # Replace characters that might be interpreted as markup or cause issues
                    safe_command = safe_command.replace("[", "【").replace("]", "】")
                    safe_command = safe_command.replace('"', "'")
                    safe_command = safe_command.replace("\\", "/")
                    
                    # Add visual indicator for selected command
                    cmd_index = i - 1
                    if cmd_index == self.selected_command_index:
                        content_lines.append(f"{cmd_emoji} ({i}) > {safe_command}")  # Add '>' to indicate selection
                    else:
                        content_lines.append(f"{cmd_emoji} ({i}) {safe_command}")
                    
                    # Store line indices for commands
                    cmd_line_index = len(content_lines) - 1  # Index of the command line
                    self.command_indices.append((i-1, cmd_line_index))
                
                # Update the existing content widget with markup disabled
                content_widget = self.query_one("#main-pane-content")
                content_widget.markup = False
                content_widget.update("\n".join(content_lines))
                
                # Force a refresh to ensure the UI updates
                self.refresh()
            else:
                # If no wish selected, show simple message
                self.mount(Static("(No wish selected)", id="main-pane-content"))
        except Exception as e:
            error_message = f"Error updating wish: {e}"
            self.log(error_message)
            try:
                content_widget = self.query_one("#main-pane-content")
                content_widget.update(f"(Error displaying wish details: {e})")
            except:
                # Minimal error handling if we can't even get the content widget
                pass
    
    def on_key(self, event) -> None:
        """Handle key events for command selection."""
        # 条件チェックを緩和し、ログを追加
        if not self.current_wish:
            self.log("on_key: No current wish")
            return False
        if not self.current_wish.command_results:
            self.log("on_key: No command results")
            return False
        # command_indicesのチェックを削除 - 常に設定されるはずなので不要

        if event.key in ("up", "arrow_up"):
            self.log(f"on_key: Up key pressed, current index: {self.selected_command_index}")
            self.select_previous_command()
            return True
        elif event.key in ("down", "arrow_down"):
            self.log(f"on_key: Down key pressed, current index: {self.selected_command_index}")
            self.select_next_command()
            return True
        
        return False
    
    def select_previous_command(self) -> None:
        """Select the previous command."""
        if self.selected_command_index > 0:
            self.selected_command_index -= 1
            self.update_command_selection()
    
    def select_next_command(self) -> None:
        """Select the next command."""
        if self.selected_command_index < len(self.current_wish.command_results) - 1:
            self.selected_command_index += 1
            self.update_command_selection()
        elif self.selected_command_index == -1 and len(self.current_wish.command_results) > 0:
            # If no command is selected yet, select the first one
            self.selected_command_index = 0
            self.update_command_selection()
    
    def update_command_selection(self) -> None:
        """Update the command selection and post a message."""
        if 0 <= self.selected_command_index < len(self.current_wish.command_results):
            selected_command = self.current_wish.command_results[self.selected_command_index]
            # Post a message that a command was selected
            self.post_message(CommandSelected(selected_command))
            
            # 選択状態を保持して表示を更新
            self.log(f"update_command_selection: selected_command_index={self.selected_command_index}")
            self.update_wish(self.current_wish, preserve_selection=True)
    
    def on_click(self, event) -> None:
        """Handle click events to select commands."""
        # 条件チェックを緩和し、ログを追加
        if not self.current_wish:
            self.log("on_click: No current wish")
            return
        if not self.current_wish.command_results:
            self.log("on_click: No command results")
            return
        # command_indicesのチェックを削除 - 常に設定されるはずなので不要
        
        try:
            # Get the clicked line
            content_widget = self.query_one("#main-pane-content")
            clicked_line = event.y - content_widget.region.y
            self.log(f"on_click: Clicked line: {clicked_line}")
            
            # Check if we clicked on a command line
            for cmd_index, line_index in self.command_indices:
                if clicked_line == line_index or clicked_line == line_index + 1:  # Command line or command text line
                    if 0 <= cmd_index < len(self.current_wish.command_results):
                        self.log(f"on_click: Selected command index: {cmd_index}")
                        self.selected_command_index = cmd_index
                        selected_command = self.current_wish.command_results[cmd_index]
                        # Post a message that a command was selected
                        self.post_message(CommandSelected(selected_command))
                        # 選択状態を保持して表示を更新
                        self.update_wish(self.current_wish, preserve_selection=True)
                        break
        except Exception as e:
            self.log(f"Error handling click: {e}")
