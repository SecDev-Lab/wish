"""Network error handler node for the command generation graph."""

import json
import logging
from typing import Annotated

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from wish_models.command_result import CommandInput
from wish_models.settings import Settings

from ..constants import DIALOG_AVOIDANCE_DOC
from ..models import GraphState
from ..utils import strip_markdown_code_block

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
        # If no failed_command_results or not a network error, return the original state
        if not state.failed_command_results or state.error_type != "NETWORK_ERROR":
            logger.info("No network error to handle")
            return state

        # Create the LLM with model_kwargs to force JSON output
        model = settings_obj.OPENAI_MODEL or "gpt-4o"
        llm = ChatOpenAI(
            model=model,
            temperature=0.2,
            model_kwargs={"response_format": {"type": "json_object"}}  # JSONレスポンスを強制
        )

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
            json.dumps([result.model_dump(mode="json") for result in state.failed_command_results], ensure_ascii=False)
            if state.failed_command_results else "[]"
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

            # LLMの応答をログ出力
            logger.info(f"LLM response: {result}")

            # マークダウン形式のコードブロック表記を削除
            result = strip_markdown_code_block(result)
        except Exception as e:
            raise RuntimeError(f"Error invoking LLM chain: {e}") from e

        # Use the result directly as a command
        command = result.strip()
        command = strip_markdown_code_block(command)

        # Default timeout value (same as the original timeout)
        timeout_sec = 60
        if state.failed_command_results and len(state.failed_command_results) > 0:
            original_timeout = state.failed_command_results[0].timeout_sec
            if original_timeout:
                timeout_sec = original_timeout

        # Create command input
        command_candidates = [CommandInput(command=command, timeout_sec=timeout_sec)]

        logger.info(f"Generated command to handle network error: {command}")

        # Update the state
        return GraphState(
            query=state.query,
            context=state.context,
            processed_query=state.processed_query,
            command_candidates=command_candidates,
            generated_commands=state.generated_commands,
            is_retry=True,
            error_type="NETWORK_ERROR",
            failed_command_results=state.failed_command_results
        )
    except Exception as e:
        raise RuntimeError("Error handling network error") from e
