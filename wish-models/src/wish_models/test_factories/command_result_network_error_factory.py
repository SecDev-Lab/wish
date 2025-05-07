"""
CommandResult のネットワークエラー用ファクトリクラス
"""

import factory

from wish_models import CommandResult, CommandState
from wish_models.test_factories.log_files_factory import LogFilesFactory
from wish_models.test_factories.utc_datetime_factory import UtcDatetimeFactory


class CommandResultNetworkErrorFactory(factory.Factory):
    """ネットワークエラーのCommandResultを生成するファクトリ"""

    class Meta:
        model = CommandResult

    num = factory.Faker("random_int", min=1)
    command = factory.Faker("sentence")
    state = CommandState.NETWORK_ERROR
    timeout_sec = 60
    exit_code = 1
    log_summary = "Connection closed by peer"
    log_files = factory.SubFactory(LogFilesFactory)
    created_at = factory.SubFactory(UtcDatetimeFactory)
    finished_at = factory.SubFactory(UtcDatetimeFactory)

    @classmethod
    def create_with_command(cls, command: str, timeout_sec: int = 60, log_summary: str = None) -> CommandResult:
        """特定のコマンドとタイムアウト値を持つCommandResultを作成する

        Args:
            command: ネットワークエラーが発生したコマンド
            timeout_sec: タイムアウト値（秒）
            log_summary: エラーログの要約（省略可）

        Returns:
            CommandResult: ネットワークエラーのCommandResult
        """
        return cls(
            command=command,
            timeout_sec=timeout_sec,
            log_summary=log_summary or "Connection closed by peer"
        )
