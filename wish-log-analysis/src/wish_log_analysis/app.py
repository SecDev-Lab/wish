import json
import logging
import os
import requests
from typing import Dict, Any, Optional

from wish_models.command_result import CommandResult

from .models import LogAnalysisInput, LogAnalysisOutput

logger = logging.getLogger(__name__)


class LogAnalysisClient:
    """
    ログ解析APIクライアント
    """
    def __init__(self, api_url: Optional[str] = None):
        self.api_url = api_url or os.environ.get("WISH_LOG_ANALYSIS_API_URL", "http://localhost:3000/analyze")
    
    def analyze(self, command_result: CommandResult) -> LogAnalysisOutput:
        """
        APIサーバーを呼び出して解析を行う
        """
        # APIリクエストの送信
        try:
            print(f"APIリクエスト送信先: {self.api_url}")
            request_data = {"command_result": command_result.model_dump()}
            print(f"リクエストデータ: {json.dumps(request_data, indent=2)}")
            
            response = requests.post(
                self.api_url,
                json=request_data,
                headers={"Content-Type": "application/json"},
                timeout=30,
            )
            print(f"レスポンスステータス: {response.status_code}")
            
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                print(f"HTTPエラー: {e}")
                print(f"レスポンス内容: {response.text}")
                raise
            
            # レスポンスの解析
            result = response.json()
            
            # サーバーからのレスポンスを適切に処理
            if "analyzed_command_result" in result:
                analyzed_result = result["analyzed_command_result"]
                return LogAnalysisOutput(
                    summary=analyzed_result.get("log_summary", "解析結果なし"),
                    state=analyzed_result.get("state", "OTHERS"),
                    error_message=result.get("error")
                )
            else:
                return LogAnalysisOutput(
                    summary="APIレスポンスの形式が不正です",
                    state="error",
                    error_message="Invalid API response format"
                )
        
        except requests.RequestException as e:
            logger.error(f"API request failed: {e}")
            # エラー時のフォールバック処理
            return LogAnalysisOutput(
                summary="APIリクエストに失敗しました",
                state="error",
                error_message=str(e),
            )


def analyze_logs(command_result: CommandResult) -> LogAnalysisOutput:
    """
    APIサーバーを呼び出して解析を行う
    """
    client = LogAnalysisClient()
    return client.analyze(command_result)


def lambda_handler(event: Dict[str, Any], context: Optional[Any] = None) -> Dict[str, Any]:
    """
    AWS Lambda handler
    """
    logger.info("Received event: %s", json.dumps(event))
    
    try:
        # APIGatewayからのイベントを処理
        if "body" in event:
            body = json.loads(event["body"])
            command_result = CommandResult(
                num=1,
                command=body.get("command", ""),
                state=body.get("state", "DOING"),
                exit_code=body.get("exit_code", 0),
                log_files={"stdout": body.get("output", ""), "stderr": ""},
                created_at=body.get("created_at", None),
            )
        else:
            # 直接呼び出しの場合
            command_result = CommandResult(
                num=1,
                command=event.get("command", ""),
                state=event.get("state", "DOING"),
                exit_code=event.get("exit_code", 0),
                log_files={"stdout": event.get("output", ""), "stderr": ""},
                created_at=event.get("created_at", None),
            )
        
        # 解析の実行
        result = analyze_logs(command_result)
        
        # レスポンスの返却
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps(result.model_dump())
        }
    
    except Exception as e:
        logger.exception("Error processing request")
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "error": str(e)
            })
        }


if __name__ == "__main__":
    # ローカルでのテスト用
    from wish_models.command_result.command_state import CommandState
    from wish_models.command_result.log_files import LogFiles
    from wish_models.utc_datetime import UtcDatetime
    
    test_command_result = CommandResult(
        num=1,
        command="ls -la",
        state=CommandState.DOING,
        exit_code=0,
        log_files=LogFiles(stdout="total 16\ndrwxr-xr-x  4 user  staff  128 Apr  2 10:00 .\ndrwxr-xr-x  3 user  staff   96 Apr  2 10:00 ..\n-rw-r--r--  1 user  staff    0 Apr  2 10:00 file1.txt\n-rw-r--r--  1 user  staff    0 Apr  2 10:00 file2.txt", stderr=""),
        created_at=UtcDatetime.now()
    )
    result = analyze_logs(test_command_result)
    print(json.dumps(result.model_dump(), indent=2))
