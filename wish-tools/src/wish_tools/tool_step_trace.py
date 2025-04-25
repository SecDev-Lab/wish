"""
ステップトレースモジュール。

このモジュールは、RapidPen-visにステップトレースを追加するためのワークフローを提供します。
"""

from typing import Dict

import requests
from langgraph.graph import END, StateGraph
from pydantic import BaseModel

from wish_tools.to_base64 import main as to_base64


class StepTraceState(BaseModel):
    """
    ステップトレースの状態を表すモデル

    Attributes:
        run_id: 実行ID（Run-プレフィックスなし）
        trace_name: トレース名
        trace_message: トレースメッセージ
        trace_message_base64: Base64エンコードされたトレースメッセージ
        response_status_code: レスポンスのステータスコード
        response_body: レスポンスのボディ
    """
    run_id: str
    trace_name: str
    trace_message: str
    trace_message_base64: str = ""
    response_status_code: int = 0
    response_body: str = ""


def encode_trace_message(state: StepTraceState) -> StepTraceState:
    """
    トレースメッセージをBase64エンコードする

    Args:
        state: 現在の状態

    Returns:
        更新された状態（Base64エンコードされたトレースメッセージを含む）
    """
    # Base64エンコード
    encoded = to_base64(state.trace_message)

    # 状態を更新
    return StepTraceState(
        run_id=state.run_id,
        trace_name=state.trace_name,
        trace_message=state.trace_message,
        trace_message_base64=encoded
    )


def post_step_trace(state: StepTraceState) -> StepTraceState:
    """
    ステップトレースをPOSTする

    Args:
        state: 現在の状態

    Returns:
        更新された状態（レスポンス情報を含む）
    """
    # POSTするデータを準備
    data = {
        "run_id": state.run_id,  # プレフィックスを追加しない
        "trace_name": state.trace_name,
        "trace_message_base64": state.trace_message_base64
    }

    try:
        # POSTリクエストを送信
        response = requests.post(
            "http://host.docker.internal:23456/api/addStepTrace",
            json=data,
            headers={"Content-Type": "application/json"}
        )

        # レスポンスを取得
        status_code = response.status_code
        body = response.text
    except Exception as e:
        # エラーが発生した場合
        status_code = 599
        body = str(e)

    # 状態を更新
    return StepTraceState(
        run_id=state.run_id,
        trace_name=state.trace_name,
        trace_message=state.trace_message,
        trace_message_base64=state.trace_message_base64,
        response_status_code=status_code,
        response_body=body
    )


def build_graph() -> StateGraph:
    """
    ステップトレースのワークフローグラフを構築する

    Returns:
        構築されたワークフローグラフ
    """
    # グラフの作成
    graph = StateGraph(StepTraceState)

    # ノードの追加
    graph.add_node("encode_trace_message", encode_trace_message)
    graph.add_node("post_step_trace", post_step_trace)

    # エッジの追加
    graph.set_entry_point("encode_trace_message")
    graph.add_edge("encode_trace_message", "post_step_trace")
    graph.add_edge("post_step_trace", END)

    return graph


def main(
    run_id: str,
    trace_name: str,
    trace_message: str
) -> Dict[str, str]:
    """
    メイン関数

    Args:
        run_id: 実行ID（Run-プレフィックスなし）
        trace_name: トレース名
        trace_message: トレースメッセージ

    Returns:
        結果を含む辞書
    """
    try:
        # グラフの構築
        graph = build_graph()

        # グラフの実行
        initial_state = StepTraceState(
            run_id=run_id,
            trace_name=trace_name,
            trace_message=trace_message
        )

        workflow = graph.compile()
        result = workflow.invoke(initial_state, {"run_name": f"Tool-StepTrace-{trace_name}"})

        # 結果を返す
        return {
            "status_code": result["response_status_code"],
            "body": result["response_body"]
        }
    except Exception as e:
        # エラーが発生した場合
        return {
            "status_code": 599,
            "body": f"Error during workflow execution: {str(e)}"
        }
