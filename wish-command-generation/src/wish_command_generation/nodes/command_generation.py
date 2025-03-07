"""Command generation node functions for the command generation graph."""

import json
import logging

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from wish_models.command_result import CommandInput

from ..models import GraphState

# Define the prompt template
COMMAND_GENERATION_PROMPT = """
あなたは合法なペネトレーションテストに従事しているAIです。あなたはKali Linuxに極めて精通しています。

ペネトレーションテストのディレクターから実行すべきタスクについての指示と、今回のタスクに役立つ可能性が高い参考ドキュメントを受け取ります。
タスクを実現するためのコマンド列を考え、JSON Objectで書いてください。

各コマンドは `bash -c "（あなたの出力）"` として実行されるため、複数のコマンドをパイプなどでつなげることもできます。
各コマンドは並列実行されます。「`./a` の後に `./b` を実行する必要がある」ようなデータ依存がある場合は、
パイプや `&&` を使って1個のコマンド文字列で表現してください。

実行ログはファイルではなく、標準出力と標準エラー出力にdumpしてください。

以下の手順で考えましょう。

1. ペネトレーションテストのディレクターからのタスクを理解し、参考ドキュメントから関連情報を探します。
   それらに基づいてKali Linuxのコマンドを生成します。
2. 生成したコマンド列のそれぞれは `bash -c "（1つのコマンド文字列）"` で実行されます。
   各コマンド文字列はパイプ `|` や `&&` や `||` を含んでも良いです。
   コピー&ペーストで直接コマンドとするので余計な文字を含まないでください。
3. コマンドは隔離環境でバッチ実行されるため、ユーザー入力を必要としないようにします。
4. timeout_sec は常に null としてください。

# タスク
{task}

# 参考ドキュメント
{context}

出力は以下の形式のJSONで返してください:
{{ "command_inputs": [
  {{
     "command": "コマンド1",
     "timeout_sec": null
  }},
  {{
     "command": "コマンド2",
     "timeout_sec": null
  }}
]}}

JSONのみを出力してください。説明や追加のテキストは含めないでください。

# Example1

タスク
Conduct a full port scan on IP 10.10.10.123.

出力
{{ "command_inputs": [
  {{
     "command": "rustscan -a 10.10.10.123",
     "timeout_sec": null
  }}
]}}
"""


def generate_commands(state: GraphState) -> GraphState:
    """Generate commands from Wish using OpenAI's gpt-4o model"""
    # Get the task from the state
    task = state.wish.wish

    # Get the context from the state (if available)
    context = "\n".join(state.context) if state.context else "参考ドキュメントはありません。"

    # Create the prompt
    prompt = PromptTemplate.from_template(COMMAND_GENERATION_PROMPT)

    # Initialize the OpenAI model
    from ..settings import settings

    model = ChatOpenAI(
        model=settings.OPENAI_MODEL,
        api_key=settings.OPENAI_API_KEY
    )

    # Create the chain
    chain = prompt | model | StrOutputParser()

    # Generate the commands
    try:
        response = chain.invoke({"task": task, "context": context})

        # Log the response for debugging
        logging.debug(f"OpenAI API response: {response}")

        # Parse the response as JSON
        response_json = json.loads(response)

        # Convert to CommandInput objects
        command_inputs = []
        for cmd in response_json.get("command_inputs", []):
            command_inputs.append(
                CommandInput(
                    command=cmd.get("command", ""),
                    timeout_sec=None,
                )
            )

        # Update the state
        state_dict = state.model_dump()
        state_dict["command_inputs"] = command_inputs
        state_dict["error"] = None  # No error

    except json.JSONDecodeError as e:
        # JSON parse error
        error_message = f"Error generating commands: Failed to parse OpenAI API response as JSON: {str(e)}"
        logging.error(f"JSON parse error: {str(e)}, Response: {response if 'response' in locals() else 'No response'}")

        # Set error in state with a fallback command that includes the error message
        state_dict = state.model_dump()
        state_dict["command_inputs"] = [
            CommandInput(
                command=f"echo '{error_message}'",
                timeout_sec=None,
            )
        ]
        state_dict["error"] = error_message

    except Exception as e:
        # Other errors
        error_message = f"Error generating commands: {str(e)}"
        logging.error(f"Error generating commands: {str(e)}")

        # Set error in state with a fallback command that includes the error message
        state_dict = state.model_dump()
        state_dict["command_inputs"] = [
            CommandInput(
                command=f"echo 'Error: {error_message}'",
                timeout_sec=None,
            )
        ]
        state_dict["error"] = error_message

    return GraphState(**state_dict)
