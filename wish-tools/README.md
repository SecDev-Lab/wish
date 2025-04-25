# RapidPen Tools

RapidPen Toolsモジュールは、RapidPenの各モジュールで使用される共通ツールを提供するモジュールです。

## 提供ツール

### Tool Step Trace

Tool Step Traceは、RapidPen-visにステップトレースを追加するためのワークフローを提供します。このツールを使用することで、ワークフローの実行状況を可視化することができます。

#### 使用方法

```python
from rapidpen_tools.tool_step_trace import main as step_trace_main

# StepTraceを呼び出し
result = step_trace_main(
    run_id="実行ID",
    trace_name="トレース名",
    trace_message="トレースメッセージ"
)
```

#### パラメータ

- `run_id`: 実行ID（Run-プレフィックスなし）
- `trace_name`: トレース名
- `trace_message`: トレースメッセージ

#### 戻り値

```python
{
    "status_code": 200,  # HTTPステータスコード
    "body": "Success"    # レスポンスボディ
}
```

### Base64 Encoder

Base64エンコーダーは、文字列をBase64形式にエンコードするためのツールを提供します。

#### 使用方法

```python
from rapidpen_tools.to_base64 import main as to_base64

# 文字列をBase64エンコード
encoded = to_base64("Hello, World!")
```

#### パラメータ

- `plain`: エンコードする文字列

#### 戻り値

Base64エンコードされた文字列
