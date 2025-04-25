"""
Integration tests for the Tool Step Trace module.
"""

from unittest.mock import MagicMock, patch

import pytest

from wish_tools.tool_step_trace import main


@pytest.mark.asyncio
@patch("wish_tools.tool_step_trace.requests.post")
async def test_step_trace_workflow(mock_post):
    """Test the Step Trace workflow."""
    print("\n=== test_step_trace_workflow ===")

    # モックの設定
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "Success"
    mock_post.return_value = mock_response
    print("HTTPレスポンスをモック:", {"status_code": 200, "body": "Success"})

    # 関数の実行
    result = main(
        run_id="test-run-id",
        trace_name="Test Trace",
        trace_message="Hello, World!"
    )

    # 結果の出力
    print("結果:", result)

    # 検証
    assert "status_code" in result
    assert "body" in result
    assert result["status_code"] == 200
    assert result["body"] == "Success"

    # モックが正しく呼び出されたことを確認
    mock_post.assert_called_once_with(
        "http://host.docker.internal:23456/api/addStepTrace",
        json={
            "run_id": "test-run-id",
            "trace_name": "Test Trace",
            "trace_message_base64": "SGVsbG8sIFdvcmxkIQ=="
        },
        headers={"Content-Type": "application/json"}
    )


@pytest.mark.asyncio
@patch("wish_tools.tool_step_trace.requests.post")
async def test_step_trace_with_error(mock_post):
    """Test the Step Trace workflow with error."""
    print("\n=== test_step_trace_with_error ===")

    # モックの設定
    mock_post.side_effect = Exception("Connection error")
    print("HTTP接続エラーをモック: Connection error")

    # 関数の実行
    result = main(
        run_id="test-run-id",
        trace_name="Test Trace",
        trace_message="Hello, World!"
    )

    # 結果の出力
    print("結果:", result)

    # 検証
    assert "status_code" in result
    assert "body" in result
    assert result["status_code"] == 599
    assert "Connection error" in result["body"]

    # モックが正しく呼び出されたことを確認
    mock_post.assert_called_once()


@pytest.mark.asyncio
@patch("wish_tools.tool_step_trace.requests.post")
async def test_step_trace_with_long_message(mock_post):
    """Test the Step Trace workflow with a long message."""
    print("\n=== test_step_trace_with_long_message ===")

    # モックの設定
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "Success"
    mock_post.return_value = mock_response
    print("HTTPレスポンスをモック:", {"status_code": 200, "body": "Success"})

    # 長いメッセージを作成
    long_message = "A" * 10000
    print(f"長いメッセージを作成: {len(long_message)}文字")

    # 関数の実行
    result = main(
        run_id="test-run-id",
        trace_name="Long Message Test",
        trace_message=long_message
    )

    # 結果の出力
    print("結果:", result)

    # 検証
    assert "status_code" in result
    assert "body" in result
    assert result["status_code"] == 200
    assert result["body"] == "Success"

    # モックが正しく呼び出されたことを確認
    mock_post.assert_called_once()
    # Base64エンコードされたメッセージの長さを確認
    args = mock_post.call_args[1]["json"]
    assert "trace_message_base64" in args
    assert len(args["trace_message_base64"]) > 13000  # Base64エンコードすると約4/3倍になる
