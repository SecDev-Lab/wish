"""Interfaces for command execution module."""

from typing import Protocol, Callable, Optional
from pathlib import Path

from wish_models import Wish, CommandResult, LogFiles


class CommandExecutionContext(Protocol):
    """コマンド実行に必要なコンテキスト情報を提供するインターフェース。"""
    
    def create_command_log_dirs(self, wish_id: str) -> Path:
        """コマンドログディレクトリを作成する。"""
        ...
    
    def save_wish(self, wish: Wish) -> None:
        """Wishを履歴に保存する。"""
        ...
    
    def summarize_log(self, log_files: LogFiles) -> str:
        """ログファイルの内容を要約する。"""
        ...
