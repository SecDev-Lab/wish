"""Command generation node functions for the command generation graph."""

import json
import logging

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from wish_models.command_result import CommandInput

from ..exceptions import CommandGenerationError
from ..models import GraphState

# Define the prompt template
COMMAND_GENERATION_PROMPT = """
あなたは合法なペネトレーションテストに従事しているAIです。あなたは様々なOSのコマンドに精通しています。

ペネトレーションテストのディレクターから実行すべきタスクについての指示と、今回のタスクに役立つ可能性が高い参考ドキュメントを受け取ります。
タスクを実現するためのコマンド列を考え、JSON Objectで書いてください。
あなたの出力はそのままパースされるので、 "```json" など余計な文字列は出力しないでください。

各コマンドは `bash -c "（あなたの出力）"` として実行されるため、複数のコマンドをパイプなどでつなげることもできます。
各コマンドは並列実行されます。「`./a` の後に `./b` を実行する必要がある」ようなデータ依存がある場合は、
パイプや `&&` を使って1個のコマンド文字列で表現してください。

実行ログはファイルではなく、標準出力と標準エラー出力にdumpしてください。

以下の手順で考えましょう。

1. ペネトレーションテストのディレクターからのタスクを理解し、参考ドキュメントから関連情報を探します。
   それらに基づいて適切なコマンドを生成します。
2. 生成したコマンド列のそれぞれは `bash -c "（1つのコマンド文字列）"` で実行されます。
   各コマンド文字列はパイプ `|` や `&&` や `||` を含んでも良いです。
3. コマンドは隔離環境でバッチ実行されるため、ユーザー入力を必要としないようにします。
4. timeout_sec は常に null としてください。
5. 実行環境のOSに適したコマンドを生成してください。
6. 2つ以上のコマンドが生成されると並列実行されるので、望ましいです。

# 実行環境情報
OS: {system_os}
アーキテクチャ: {system_arch}
バージョン: {system_version}

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

実行環境情報
OS: Linux
アーキテクチャ: x86_64
バージョン: 5.15.0-kali3-amd64

タスク
Conduct a full port scan on IP 10.10.10.123.

出力
{{ "command_inputs": [
  {{
     "command": "rustscan -a 10.10.10.123",
     "timeout_sec": null
  }}
]}}

# Example2

実行環境情報
OS: Windows
アーキテクチャ: AMD64
バージョン: 10.0.19044

タスク
List all hidden files in the current directory.

出力
{{ "command_inputs": [
  {{
     "command": "dir /a:h",
     "timeout_sec": null
  }}
]}}

# Example3

実行環境情報
OS: Darwin
アーキテクチャ: arm64
バージョン: 22.4.0

タスク
List all hidden files in the current directory.

出力
{{ "command_inputs": [
  {{
     "command": "ls -la | grep '^\\.'",
     "timeout_sec": null
  }}
]}}
"""


def generate_commands(state: GraphState, settings_obj) -> GraphState:
    """Generate commands from Wish using OpenAI's gpt-4o model"""
    # Get the task from the state
    task = state.wish.wish

    # Get the context from the state (if available)
    context = "\n".join(state.context) if state.context else "参考ドキュメントはありません。"

    # Get system info (if available)
    system_os = "Unknown"  # Default value
    system_arch = "Unknown"  # Default value
    system_version = "Unknown"  # Default value

    if hasattr(state, 'system_info') and state.system_info:
        system_os = state.system_info.os
        system_arch = state.system_info.arch
        system_version = state.system_info.version or "Unknown"

    # Create the prompt
    prompt = PromptTemplate.from_template(COMMAND_GENERATION_PROMPT)

    # Initialize the OpenAI model
    model = ChatOpenAI(
        model=settings_obj.OPENAI_MODEL,
        api_key=settings_obj.OPENAI_API_KEY,
        use_responses_api=True
    )

    # Create the chain
    chain = prompt | model | StrOutputParser()

    # Generate the commands
    state_dict = state.model_dump()

    try:
        response = chain.invoke({
            "task": task,
            "context": context,
            "system_os": system_os,
            "system_arch": system_arch,
            "system_version": system_version
        })

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
        state_dict["command_inputs"] = command_inputs
        state_dict["error"] = None  # No error

    except json.JSONDecodeError as e:
        # JSON parse error
        error_message = f"Command generation failed: Invalid JSON format: {str(e)}"
        api_response = response if 'response' in locals() else 'No response'
        logging.error(f"JSON parse error: {str(e)}, Response: {api_response}")

        # Set error in state
        state_dict["command_inputs"] = [
            CommandInput(
                command=f"Error generating commands: Failed to parse JSON: {str(e)}",
                timeout_sec=None,
            )
        ]
        state_dict["error"] = error_message

        # Raise custom exception with structured data
        raise CommandGenerationError(f"{error_message}. Response: {api_response}", api_response) from e

    except Exception as e:
        # Other errors
        error_message = f"Command generation failed: {str(e)}"
        api_response = response if 'response' in locals() else None
        logging.error(f"Error generating commands: {str(e)}")

        # Set error in state
        state_dict["command_inputs"] = [
            CommandInput(
                command=f"Error generating commands: {str(e)}",
                timeout_sec=None,
            )
        ]
        state_dict["error"] = error_message

        # Raise custom exception with structured data
        if api_response:
            raise CommandGenerationError(error_message, api_response) from e
        else:
            raise CommandGenerationError(error_message) from e

    return GraphState(**state_dict)
