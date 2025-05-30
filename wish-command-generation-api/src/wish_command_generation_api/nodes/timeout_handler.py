"""Timeout handler node for the command generation graph."""

import json
import logging
from typing import Annotated

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from wish_models.command_result import CommandInput
from wish_models.settings import Settings

from ..constants import DIVIDE_AND_CONQUER_DOC, FAST_ALTERNATIVE_DOC
from ..models import GraphState
from ..utils import strip_markdown_code_block

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handle_timeout(state: Annotated[GraphState, "Current state"], settings_obj: Settings) -> GraphState:
    """Handle timeout errors by applying fast alternatives or divide-and-conquer strategies.

    Args:
        state: The current graph state.

    Returns:
        Updated graph state with modified commands.
    """
    try:
        # If no act_result or not a timeout error, return the original state
        if not state.failed_command_results or state.error_type != "TIMEOUT":
            logger.info("No timeout error to handle")
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
            """あなたは合法なペネトレーションテストに従事しているAIです。

ペネトレーションテストのディレクターから以下を受け取ります。
- 実行すべき「タスク」の指示
- あなたが以前出力しTIMEOUTとなったコマンドについての「フィードバック」
- 今回のタスクに役立つ可能性が高い「参考ドキュメント」
- コマンド高速化のための「高速な代替コマンド案」
- コマンド並列化のための「分割統治案」

フィードバックのコマンド列を、次はタイムアウトを起こさないものに修正してください。

各コマンドは `bash -c "（あなたの出力）"` として実行されるため、複数のコマンドをパイプなどでつなげることもできます。
各コマンドは並列実行されます。「`./a` の後に `./b` を実行する必要がある」ようなデータ依存がある場合は、
パイプや `&&` を使って1個のコマンド文字列で表現してください。

実行ログはファイルではなく、標準出力と標準エラー出力にdumpしてください。

以下の手順で考えましょう。

1. 「タスク」を理解し、「参考ドキュメント」から関連情報を探します。
2. 「フィードバック」から、前に使用したコマンドを確認します。
3. 前に使用したコマンドに「高速な代替コマンド案」があれば、それを使ったコマンドを出力し、
   strategyを"fast_alternative"に設定してください。
4. さもなければ、前に使用したコマンドに「分割統治案」があれば、それを使ったコマンドを出力し、
   strategyを"divide_and_conquer"に設定してください。
5. さもなければ、前に使用したコマンドと同じコマンドを出力し、strategyを"same_command"に設定してください。
   タイムアウト値は「フィードバック」のものをそのまま出力してください。後ほどLLMを利用せずに調整します。

# タスク
{query}

# フィードバック
{feedback}

# 参考ドキュメント
{context}

# 高速な代替コマンド案
{fast_alternative_doc}

# 分割統治案
{divide_and_conquer_doc}

出力は以下の形式のJSONで返してください:
{{ "command_inputs": [
  {{
     "command": "コマンド1",
     "strategy": "fast_alternative|divide_and_conquer|same_command",
     "timeout_sec": タイムアウト秒数（数値）
  }},
  {{
     "command": "コマンド2",
     "strategy": "fast_alternative|divide_and_conquer|same_command",
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

        # Create the chain
        chain = prompt | llm | StrOutputParser()

        # Invoke the chain
        result = chain.invoke({
            "query": state.query,
            "feedback": feedback_str,
            "context": context_str,
            "fast_alternative_doc": FAST_ALTERNATIVE_DOC,
            "divide_and_conquer_doc": DIVIDE_AND_CONQUER_DOC
        })

        # LLMの応答をログ出力
        logger.info(f"LLM response: {result}")

        # マークダウン形式のコードブロック表記を削除
        result = strip_markdown_code_block(result)

        # Use the result directly as a command
        command = result.strip()
        command = strip_markdown_code_block(command)

        # Default timeout value (double the original timeout)
        timeout_sec = 60
        if state.failed_command_results and len(state.failed_command_results) > 0:
            original_timeout = state.failed_command_results[0].timeout_sec
            if original_timeout:
                timeout_sec = original_timeout * 2

        # Create command input
        command_candidates = [CommandInput(command=command, timeout_sec=timeout_sec)]

        logger.info(f"Generated command to handle timeout: {command}")

        # Update the state
        return GraphState(
            query=state.query,
            context=state.context,
            processed_query=state.processed_query,
            command_candidates=command_candidates,
            generated_commands=state.generated_commands,
            is_retry=True,
            error_type="TIMEOUT",
            failed_command_results=state.failed_command_results
        )
    except Exception as e:
        raise RuntimeError("Error handling timeout") from e
