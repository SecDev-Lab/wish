"""Network error handler node for the command generation graph."""

import json
import logging
from typing import Annotated, List

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from wish_models.command_result import CommandInput
from wish_models.settings import Settings

from ..constants import DEFAULT_TIMEOUT_SEC, DIALOG_AVOIDANCE_DOC
from ..models import GraphState

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handle_network_error(state: Annotated[GraphState, "Current state"], settings_obj: Settings) -> GraphState:
    """Handle network errors by generating retry commands.

    Args:
        state: The current graph state.

    Returns:
        Updated graph state with retry commands.
    """
    try:
        # If no act_result or not a network error, return the original state
        if not state.act_result or state.error_type != "NETWORK_ERROR":
            logger.info("No network error to handle")
            return state

        # Create the LLM
        model = settings_obj.OPENAI_MODEL or "gpt-4o"
        llm = ChatOpenAI(model=model, temperature=0.2)

        # Create the prompt
        prompt = ChatPromptTemplate.from_template(
            """あなたは合法なペネトレーションテストに従事しているAIです。あなたはKali Linuxに極めて精通しています。

ペネトレーションテストのディレクターから実行すべきタスクについての指示と、今回のタスクに役立つ可能性が高い参考ドキュメントを受け取ります。
タスクを実現するためのコマンド列を考え、JSONのArray of stringで書いてください。

フィードバックにあなたが以前出力したコマンド列とその実行結果があります。一部、NETWORK_ERRORが含まれるようです。
今回はエラーのない実行を目指しましょう。

各コマンドは `bash -c "（あなたの出力）"` として実行されるため、複数のコマンドをパイプなどでつなげることもできます。
各コマンドは並列実行されます。「`./a` の後に `./b` を実行する必要がある」ようなデータ依存がある場合は、
パイプや `&&` や `||` を含んでも良いです。コピー&ペーストで直接コマンドとするので余計な文字を含まないでください。

実行ログはファイルではなく、標準出力と標準エラー出力にdumpしてください。

以下の手順で考えましょう。

1. ペネトレーションテストのディレクターからのタスクを理解し、参考ドキュメントから関連情報を探します。
   それらに基づいてKali Linuxのコマンドを生成します。
2. 生成したコマンド列のそれぞれは `bash -c "（1つのコマンド文字列）"` で実行されます。
   各コマンド文字列はパイプ `|` や `&&` や `||` を含んでも良いです。
   コピー&ペーストで直接コマンドとするので余計な文字を含まないでください。
3. コマンドは隔離環境でバッチ実行されるため、ユーザー入力を必要としないようにします。
4. NETWORK_ERRORとなったコマンドは、単純に再実行すれば成功しそうならば同じコマンドを再度生成してください。
   そうでなければ、より信頼性の高い代替コマンドを考えてください。

# タスク
{query}

# フィードバック
{feedback}

# 参考ドキュメント
{context}

# 対話回避ガイドライン
{dialog_avoidance_doc}

出力は以下の形式のJSONで返してください:
{{ "command_inputs": [
  {{
     "command": "コマンド1",
     "timeout_sec": タイムアウト秒数（数値）
  }},
  {{
     "command": "コマンド2",
     "timeout_sec": タイムアウト秒数（数値）
  }}
]}}

JSONのみを出力してください。説明や追加のテキストは含めないでください。
"""
        )

        # Format the feedback as JSON string
        feedback_str = (
            json.dumps([result.model_dump() for result in state.act_result], ensure_ascii=False)
            if state.act_result else "[]"
        )

        # Format the context
        context_str = ""
        if isinstance(state.context, dict) and "history" in state.context:
            context_str = "Command History:\n" + "\n".join(state.context["history"])
        elif isinstance(state.context, dict):
            context_str = json.dumps(state.context, ensure_ascii=False)
        else:
            context_str = "No context available"

        try:
            # Create the chain
            chain = prompt | llm | StrOutputParser()

            # Invoke the chain
            result = chain.invoke({
                "query": state.query,
                "feedback": feedback_str,
                "context": context_str,
                "dialog_avoidance_doc": DIALOG_AVOIDANCE_DOC
            })
        except Exception as e:
            logger.exception(f"Error invoking LLM chain: {e}")
            # Get the original command from the act_result
            original_command = state.act_result[0].command if state.act_result else "echo 'No command found'"
            return GraphState(
                query=state.query,
                context=state.context,
                processed_query=state.processed_query,
                command_candidates=[CommandInput(command=original_command, timeout_sec=DEFAULT_TIMEOUT_SEC)],
                generated_commands=state.generated_commands,
                is_retry=True,
                error_type="NETWORK_ERROR",
                act_result=state.act_result
            )

        # Parse the result
        try:
            response_json = json.loads(result)

            # Extract commands
            command_candidates: List[CommandInput] = []
            for cmd_input in response_json.get("command_inputs", []):
                command = cmd_input.get("command", "")
                timeout_sec = cmd_input.get("timeout_sec", DEFAULT_TIMEOUT_SEC)
                if command:
                    command_candidates.append(CommandInput(command=command, timeout_sec=timeout_sec))

            if not command_candidates:
                logger.warning("No valid commands found in LLM response")
                command_candidates = [
                    CommandInput(
                        command="echo 'No valid commands generated'",
                        timeout_sec=DEFAULT_TIMEOUT_SEC
                    )
                ]

            logger.info(f"Generated {len(command_candidates)} commands to handle network error")

            # Update the state
            return GraphState(
                query=state.query,
                context=state.context,
                processed_query=state.processed_query,
                command_candidates=command_candidates,
                generated_commands=state.generated_commands,
                is_retry=True,
                error_type="NETWORK_ERROR",
                act_result=state.act_result
            )
        except json.JSONDecodeError:
            logger.error(f"Failed to parse LLM response as JSON: {result}")
            # Return the original state with a fallback command
            return GraphState(
                query=state.query,
                context=state.context,
                processed_query=state.processed_query,
                command_candidates=[
                    CommandInput(
                        command="echo 'Failed to generate network error handling command'",
                        timeout_sec=DEFAULT_TIMEOUT_SEC
                    )
                ],
                generated_commands=state.generated_commands,
                is_retry=True,
                error_type="NETWORK_ERROR",
                act_result=state.act_result,
                api_error=True
            )
    except Exception:
        logger.exception("Error handling network error")
        # Return the original state with a fallback command
        return GraphState(
            query=state.query,
            context=state.context,
            processed_query=state.processed_query,
            command_candidates=[
                CommandInput(
                    command="echo 'Error handling network error'",
                    timeout_sec=DEFAULT_TIMEOUT_SEC
                )
            ],
            generated_commands=state.generated_commands,
            is_retry=True,
            error_type="NETWORK_ERROR",
            act_result=state.act_result,
            api_error=True
        )
