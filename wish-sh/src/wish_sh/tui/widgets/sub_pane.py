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
    
    def update_command_output(self, command_result):
        """Update the pane with command output details.
        
        Args:
            command_result: The command result to display.
        """
        try:
            self.current_command = command_result
            
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
                        # Read the first few lines of stdout
                        with open(command_result.log_files.stdout, "r") as f:
                            stdout_lines = f.readlines()[:20]  # First 20 lines only
                        
                        if stdout_lines:
                            stdout_text = "".join(stdout_lines)
                            if len(stdout_lines) == 20:
                                stdout_text += "\n... (output truncated)"
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
                        # Read the first few lines of stderr
                        with open(command_result.log_files.stderr, "r") as f:
                            stderr_lines = f.readlines()[:20]  # First 20 lines only
                        
                        if stderr_lines:
                            stderr_text = "".join(stderr_lines)
                            if len(stderr_lines) == 20:
                                stderr_text += "\n... (output truncated)"
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
                        # Read the first few lines of stdout
                        with open(command_result.log_files.stdout, "r") as f:
                            stdout_lines = f.readlines()[:20]  # First 20 lines only
                        
                        if stdout_lines:
                            for line in stdout_lines:
                                # Escape any markup in the output
                                escaped_line = escape(line.rstrip())
                                content_lines.append(escaped_line)
                            if len(stdout_lines) == 20:
                                content_lines.append("... (output truncated)")
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
                        # Read the first few lines of stderr
                        with open(command_result.log_files.stderr, "r") as f:
                            stderr_lines = f.readlines()[:20]  # First 20 lines only
                        
                        if stderr_lines:
                            for line in stderr_lines:
                                # Escape any markup in the error output
                                escaped_line = escape(line.rstrip())
                                content_lines.append(escaped_line)
                            if len(stderr_lines) == 20:
                                content_lines.append("... (output truncated)")
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
                        # Read the first few lines of stdout
                        with open(command_result.log_files.stdout, "r") as f:
                            stdout_lines = f.readlines()[:20]  # First 20 lines only
                        
                        if stdout_lines:
                            for line in stdout_lines:
                                # Replace problematic characters in output
                                safe_line = line.rstrip()
                                safe_line = safe_line.replace("[", "【").replace("]", "】")
                                safe_line = safe_line.replace('"', "'")
                                safe_line = safe_line.replace("\\", "/")
                                content_lines.append(safe_line)
                            if len(stdout_lines) == 20:
                                content_lines.append("... (output truncated)")
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
                        # Read the first few lines of stderr
                        with open(command_result.log_files.stderr, "r") as f:
                            stderr_lines = f.readlines()[:20]  # First 20 lines only
                        
                        if stderr_lines:
                            for line in stderr_lines:
                                # Replace problematic characters in error output
                                safe_line = line.rstrip()
                                safe_line = safe_line.replace("[", "【").replace("]", "】")
                                safe_line = safe_line.replace('"', "'")
                                safe_line = safe_line.replace("\\", "/")
                                content_lines.append(safe_line)
                            if len(stderr_lines) == 20:
                                content_lines.append("... (output truncated)")
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
