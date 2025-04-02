from wish_log_analysis.app import LogAnalysisClient
from wish_models.command_result import CommandResult
from wish_models.command_result.command_state import CommandState
from wish_models.command_result.log_files import LogFiles
from wish_models.utc_datetime import UtcDatetime

# クライアントの初期化
client = LogAnalysisClient()  # デフォルトでは http://localhost:3001/analyze を使用

# コマンド結果の作成
command_result = CommandResult(
    num=1,
    command="ls -la",
    state=CommandState.DOING,
    exit_code=0,
    log_files=LogFiles(stdout="file1.txt file2.txt", stderr=""),
    created_at=UtcDatetime.now()
)

# コマンド結果の分析
analyzed_result = client.analyze(command_result)

# 結果の表示
print(analyzed_result)
