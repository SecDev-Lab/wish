from wish_log_analysis.app import LogAnalysisClient
from wish_models.command_result import CommandResult
from wish_models.command_result.command_state import CommandState
from wish_models.command_result.log_files import LogFiles
from wish_models.utc_datetime import UtcDatetime

# クライアントの初期化
client = LogAnalysisClient("http://localhost:3000/analyze")  # サーバーのURLを明示的に指定

# コマンド結果の作成
command_result = CommandResult(
    num=1,
    command="ls -la",
    state=CommandState.DOING,
    exit_code=0,
    log_files=LogFiles(stdout="file1.txt file2.txt", stderr="dummy.txt"),  # stderrに実際のファイル名を設定
    created_at=UtcDatetime.now()
)

try:
    # コマンド結果の分析
    analyzed_result = client.analyze(command_result)

    # 結果の表示
    print("解析結果:")
    print(f"summary: {analyzed_result.summary}")
    print(f"state: {analyzed_result.state}")
    if analyzed_result.error_message:
        print(f"error_message: {analyzed_result.error_message}")
except Exception as e:
    print(f"エラーが発生しました: {e}")
