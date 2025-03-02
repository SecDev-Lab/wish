"""Sub Pane widget for wish-sh TUI."""

import os
from textual.app import ComposeResult
from textual.widgets import Static
from textual.containers import Horizontal
from rich.markup import escape

from wish_sh.tui.widgets.base_pane import BasePane


class SubPane(BasePane):
    """Sub content pane for displaying command output details."""

    # CSS moved to external file: wish_tui.css

    def __init__(self, *args, **kwargs):
        """Initialize the SubPane.
        
        Args:
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(*args, **kwargs)
        self.current_command = None

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        yield Static("(Select a command to view details)", id="sub-pane-content")
    
    def update_for_new_wish_mode(self):
        """Update the pane for New Wish mode."""
        # Remove old grid if exists
        try:
            old_grid = self.query_one("#command-details-grid")
            self.remove(old_grid)
        except:
            pass
            
        content_widget = self.query_one("#sub-pane-content")
        content_widget.update("新しいWishのコマンド出力がここに表示されます。")
    
    def set_active(self, active: bool) -> None:
        """Set the active state of the pane.
        
        Args:
            active: Whether the pane should be active or not.
        """
        super().set_active(active)
        
        if active:
            # コンテンツウィジェットにフォーカスを当てる
            try:
                content = self.query_one("#sub-pane-content")
                content.focus()
                self.log("SubPane content focused")
            except Exception as e:
                self.log(f"Error focusing content: {e}")
    
    def on_key(self, event) -> None:
        """キーイベントを処理する
        
        Args:
            event: キーイベント
            
        Returns:
            bool: イベントが処理された場合はTrue、そうでない場合はFalse
        """
        self.log(f"SubPane on_key: {event.key}, focused: {self.has_focus}, active: {self.has_class('active-pane')}, current_command: {self.current_command is not None}")
        
        # ログビューアーダイアログを表示するキー
        if event.key == "o" and self.current_command:
            self.log(f"SubPane: 'o' key pressed with current_command: {self.current_command}")
            # stdoutのポップアップを表示
            if self.current_command.log_files and self.current_command.log_files.stdout:
                try:
                    if os.path.exists(self.current_command.log_files.stdout):
                        with open(self.current_command.log_files.stdout, "r") as f:
                            stdout_content = f.read()
                        
                        # ポップアップダイアログを表示
                        from wish_sh.tui.screens.log_viewer_screen import LogViewerScreen
                        self.app.push_screen(
                            LogViewerScreen(stdout_content, "Standard Output")
                        )
                        return True
                except Exception as e:
                    self.log(f"Error reading stdout: {e}")
            return True
        
        elif event.key == "e" and self.current_command:
            self.log(f"SubPane: 'e' key pressed with current_command: {self.current_command}")
            # stderrのポップアップを表示
            if self.current_command.log_files and self.current_command.log_files.stderr:
                try:
                    if os.path.exists(self.current_command.log_files.stderr):
                        with open(self.current_command.log_files.stderr, "r") as f:
                            stderr_content = f.read()
                        
                        # ポップアップダイアログを表示
                        from wish_sh.tui.screens.log_viewer_screen import LogViewerScreen
                        self.app.push_screen(
                            LogViewerScreen(stderr_content, "Standard Error")
                        )
                        return True
                except Exception as e:
                    self.log(f"Error reading stderr: {e}")
            return True
        
        # 既存のキーバインディング処理
        elif event.key == "j" or event.key == "down":
            content = self.query_one("#sub-pane-content")
            content.scroll_down()
            self.log("Scrolling down")
            return True
        elif event.key == "k" or event.key == "up":
            content = self.query_one("#sub-pane-content")
            content.scroll_up()
            self.log("Scrolling up")
            return True
        elif event.key == "ctrl+f":
            content = self.query_one("#sub-pane-content")
            content.scroll_page_down()
            self.log("Page down")
            return True
        elif event.key == "ctrl+b":
            content = self.query_one("#sub-pane-content")
            content.scroll_page_up()
            self.log("Page up")
            return True
        elif event.key == "<":
            content = self.query_one("#sub-pane-content")
            content.scroll_home()
            self.log("Scroll to top")
            return True
        elif event.key == ">":
            content = self.query_one("#sub-pane-content")
            content.scroll_end()
            self.log("Scroll to bottom")
            return True
        
        return False
    
    def update_command_output(self, command_result):
        """Update the pane with command output details.
        
        Args:
            command_result: The command result to display.
        """
        try:
            self.log(f"SubPane update_command_output: command_result={command_result is not None}")
            self.current_command = command_result
            self.log(f"SubPane update_command_output: self.current_command={self.current_command is not None}")
            
            # Get existing content widget
            try:
                content = self.query_one("#sub-pane-content")
            except:
                # Create a new content widget if it doesn't exist
                content = Static(id="sub-pane-content")
                self.mount(content)
            
            if not command_result:
                content.update("(No command selected)")
                return
            
            # Create two separate widgets: one for labels (with markup) and one for values (without markup)
            # Format command details as text
            label_lines = []
            value_lines = []
            
            # Add command - with label and value separated
            label_lines.append("[b]Command:[/b]")
            value_lines.append(command_result.command)
            
            label_lines.append("")
            value_lines.append("")
            
            # Add stdout content if available
            label_lines.append("[b]Standard Output:[/b]")
            
            if command_result.log_files and command_result.log_files.stdout:
                try:
                    # Check if the file exists
                    if os.path.exists(command_result.log_files.stdout):
                        # Read all lines of stdout
                        with open(command_result.log_files.stdout, "r") as f:
                            stdout_lines = f.readlines()
                        
                        if stdout_lines:
                            stdout_text = "".join(stdout_lines)
                            value_lines.append(stdout_text)
                        else:
                            value_lines.append("(No output)")
                    else:
                        value_lines.append(f"(Output file not found: {command_result.log_files.stdout})")
                except Exception as e:
                    value_lines.append(f"(Error reading output: {e})")
            else:
                value_lines.append("(No output file available)")
            
            # Add stderr content if available
            label_lines.append("")
            value_lines.append("")
            
            label_lines.append("[b]Standard Error:[/b]")
            
            if command_result.log_files and command_result.log_files.stderr:
                try:
                    # Check if the file exists
                    if os.path.exists(command_result.log_files.stderr):
                        # Read all lines of stderr
                        with open(command_result.log_files.stderr, "r") as f:
                            stderr_lines = f.readlines()
                        
                        if stderr_lines:
                            stderr_text = "".join(stderr_lines)
                            value_lines.append(stderr_text)
                        else:
                            value_lines.append("(No error output)")
                    else:
                        value_lines.append(f"(Error file not found: {command_result.log_files.stderr})")
                except Exception as e:
                    value_lines.append(f"(Error reading error output: {e})")
            else:
                value_lines.append("(No error output)")
            
            # Remove old grid if exists (but keep the content widget)
            try:
                old_grid = self.query_one("#command-details-grid")
                self.remove(old_grid)
            except:
                pass
            
            # Create content lines for the widget
            content_lines = []
            
            # Add command with label and value on the same line
            # Use rich.markup.escape to escape any markup in the command text
            escaped_command = escape(command_result.command)
            content_lines.append(f"[b]Command:[/b] {escaped_command}")
            content_lines.append("")
            
            # Add stdout content if available
            content_lines.append("[b]Standard Output:[/b]")
            
            if command_result.log_files and command_result.log_files.stdout:
                try:
                    # Check if the file exists
                    if os.path.exists(command_result.log_files.stdout):
                        # Read all lines of stdout
                        with open(command_result.log_files.stdout, "r") as f:
                            stdout_lines = f.readlines()
                        
                        if stdout_lines:
                            # Add line count information
                            content_lines.append(f"({len(stdout_lines)} lines total)")
                            
                            for line in stdout_lines:
                                # Escape any markup in the output
                                escaped_line = escape(line.rstrip())
                                content_lines.append(escaped_line)
                        else:
                            content_lines.append("(No output)")
                    else:
                        content_lines.append(f"(Output file not found: {command_result.log_files.stdout})")
                except Exception as e:
                    content_lines.append(f"(Error reading output: {e})")
            else:
                content_lines.append("(No output file available)")
            
            # Add stderr content if available
            content_lines.append("")
            content_lines.append("[b]Standard Error:[/b]")
            
            if command_result.log_files and command_result.log_files.stderr:
                try:
                    # Check if the file exists
                    if os.path.exists(command_result.log_files.stderr):
                        # Read all lines of stderr
                        with open(command_result.log_files.stderr, "r") as f:
                            stderr_lines = f.readlines()
                        
                        if stderr_lines:
                            # Add line count information
                            content_lines.append(f"({len(stderr_lines)} lines total)")
                            
                            for line in stderr_lines:
                                # Escape any markup in the error output
                                escaped_line = escape(line.rstrip())
                                content_lines.append(escaped_line)
                        else:
                            content_lines.append("(No error output)")
                    else:
                        content_lines.append(f"(Error file not found: {command_result.log_files.stderr})")
                except Exception as e:
                    content_lines.append(f"(Error reading error output: {e})")
            else:
                content_lines.append("(No error output)")
            
            # Create a simple content widget with both label and value - NO MARKUP
            content_lines = []
            
            # Add command with label and value on the same line
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
            safe_command = command_result.command
            # Replace characters that might be interpreted as markup or cause issues
            safe_command = safe_command.replace("[", "【").replace("]", "】")
            safe_command = safe_command.replace('"', "'")
            safe_command = safe_command.replace("\\", "/")
            
            content_lines.append(f"Command: {safe_command}")
            content_lines.append("")
            
            # Add stdout content if available
            content_lines.append("Standard Output:")
            
            if command_result.log_files and command_result.log_files.stdout:
                try:
                    # Check if the file exists
                    if os.path.exists(command_result.log_files.stdout):
                        # Read all lines of stdout
                        with open(command_result.log_files.stdout, "r") as f:
                            stdout_lines = f.readlines()
                        
                        if stdout_lines:
                            # Add line count information
                            content_lines.append(f"({len(stdout_lines)} lines total)")
                            
                            # 冒頭3行だけ表示
                            for line in stdout_lines[:3]:
                                # Replace problematic characters in output
                                safe_line = line.rstrip()
                                safe_line = safe_line.replace("[", "【").replace("]", "】")
                                safe_line = safe_line.replace('"', "'")
                                safe_line = safe_line.replace("\\", "/")
                                content_lines.append(safe_line)
                            
                            # 3行以上ある場合は「もっと見る」メッセージを表示
                            if len(stdout_lines) > 3:
                                content_lines.append("... (Press 'o' to view full output)")
                        else:
                            content_lines.append("(No output)")
                    else:
                        content_lines.append(f"(Output file not found: {command_result.log_files.stdout})")
                except Exception as e:
                    content_lines.append(f"(Error reading output: {e})")
            else:
                content_lines.append("(No output file available)")
            
            # Add stderr content if available
            content_lines.append("")
            content_lines.append("Standard Error:")
            
            if command_result.log_files and command_result.log_files.stderr:
                try:
                    # Check if the file exists
                    if os.path.exists(command_result.log_files.stderr):
                        # Read all lines of stderr
                        with open(command_result.log_files.stderr, "r") as f:
                            stderr_lines = f.readlines()
                        
                        if stderr_lines:
                            # Add line count information
                            content_lines.append(f"({len(stderr_lines)} lines total)")
                            
                            # 冒頭3行だけ表示
                            for line in stderr_lines[:3]:
                                # Replace problematic characters in error output
                                safe_line = line.rstrip()
                                safe_line = safe_line.replace("[", "【").replace("]", "】")
                                safe_line = safe_line.replace('"', "'")
                                safe_line = safe_line.replace("\\", "/")
                                content_lines.append(safe_line)
                            
                            # 3行以上ある場合は「もっと見る」メッセージを表示
                            if len(stderr_lines) > 3:
                                content_lines.append("... (Press 'e' to view full error output)")
                        else:
                            content_lines.append("(No error output)")
                    else:
                        content_lines.append(f"(Error file not found: {command_result.log_files.stderr})")
                except Exception as e:
                    content_lines.append(f"(Error reading error output: {e})")
            else:
                content_lines.append("(No error output)")
            
            # Update the existing content widget with markup disabled
            content_widget = self.query_one("#sub-pane-content")
            content_widget.markup = False
            content_widget.update("\n".join(content_lines))
            
            # Reset scroll position to the top
            content_widget.scroll_home()
            
            # Force a refresh to ensure the UI updates
            self.refresh()
        except Exception as e:
            self.log(f"Error updating command output: {e}")
            try:
                content_widget = self.query_one("#sub-pane-content")
                content_widget.update(f"(Error displaying command output: {e})")
            except:
                # Minimal error handling
                pass
