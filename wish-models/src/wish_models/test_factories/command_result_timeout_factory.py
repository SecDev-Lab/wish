"""
CommandResult のタイムアウトエラー用ファクトリクラス
"""

import factory

from wish_models import CommandResult, CommandState
from wish_models.test_factories.log_files_factory import LogFilesFactory
from wish_models.test_factories.utc_datetime_factory import UtcDatetimeFactory


class CommandResultTimeoutFactory(factory.Factory):
    """タイムアウトエラーのCommandResultを生成するファクトリ"""

    class Meta:
        model = CommandResult

    num = factory.Faker("random_int", min=1)
    command = factory.Faker("sentence")
    state = CommandState.TIMEOUT
    timeout_sec = 60
    exit_code = 1
    log_summary = "Command timed out"
    log_files = factory.SubFactory(LogFilesFactory)
    created_at = factory.SubFactory(UtcDatetimeFactory)
    finished_at = factory.SubFactory(UtcDatetimeFactory)

    @classmethod
    def create_with_command(cls, command: str, timeout_sec: int = 60) -> CommandResult:
        """特定のコマンドとタイムアウト値を持つCommandResultを作成する

        Args:
            command: タイムアウトしたコマンド
            timeout_sec: タイムアウト値（秒）

        Returns:
            CommandResult: タイムアウトエラーのCommandResult
        """
        return cls(
            command=command,
            timeout_sec=timeout_sec
        )
