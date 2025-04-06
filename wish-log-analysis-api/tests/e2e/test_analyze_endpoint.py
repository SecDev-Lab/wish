"""E2E tests for the /analyze endpoint."""

import os
import json
import pytest
import requests
from dotenv import load_dotenv

from wish_models.test_factories.command_result_factory import CommandResultSuccessFactory


def test_analyze_endpoint_success():
    """Test the /analyze endpoint with a successful command result.
    
    This test sends a request to the deployed API endpoint and verifies
    that it returns a 200 OK response with the expected structure.
    """
    # 環境変数の読み込み
    load_dotenv()
    
    # 環境変数のチェック
    api_endpoint = os.environ.get("API_ENDPOINT")
    api_key = os.environ.get("API_KEY")
    
    missing_vars = []
    if not api_endpoint:
        missing_vars.append("API_ENDPOINT")
    if not api_key:
        missing_vars.append("API_KEY")
    
    if missing_vars:
        pytest.skip(f"必要な環境変数が設定されていません: {', '.join(missing_vars)}")
    
    # テストデータの作成
    command_result = CommandResultSuccessFactory.build()
    
    # リクエストの送信
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key
    }
    
    payload = {
        "command_result": command_result.model_dump()
    }
    
    try:
        response = requests.post(
            f"{api_endpoint}/analyze",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        # エラーレスポンスの詳細表示
        if response.status_code != 200:
            print(f"\n===== エラーレスポンス =====")
            print(f"ステータスコード: {response.status_code}")
            print(f"レスポンスヘッダー: {response.headers}")
            try:
                error_json = response.json()
                print(f"レスポンスボディ (JSON): {json.dumps(error_json, indent=2, ensure_ascii=False)}")
            except ValueError:
                print(f"レスポンスボディ (テキスト): {response.text}")
            print("==========================\n")
        
        # レスポンスの検証
        assert response.status_code == 200, f"APIが200以外のステータスコードを返しました: {response.status_code}"
        
        try:
            response_data = response.json()
        except ValueError as e:
            pytest.fail(f"レスポンスがJSONではありません: {e}\nレスポンス: {response.text}")
        
        assert "analyzed_command_result" in response_data, "レスポンスに 'analyzed_command_result' が含まれていません"
        assert response_data.get("error") is None, f"エラーが返されました: {response_data.get('error')}"
        
        analyzed_result = response_data["analyzed_command_result"]
        assert analyzed_result["num"] == command_result.num, f"numが一致しません: 期待値={command_result.num}, 実際={analyzed_result['num']}"
        assert analyzed_result["command"] == command_result.command, f"commandが一致しません: 期待値={command_result.command}, 実際={analyzed_result['command']}"
        assert "log_summary" in analyzed_result, "レスポンスに 'log_summary' が含まれていません"
        assert "state" in analyzed_result, "レスポンスに 'state' が含まれていません"
        
    except requests.RequestException as e:
        pytest.fail(f"APIリクエスト中にエラーが発生しました: {e}")
