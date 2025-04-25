"""Command modifier node for the command generation graph."""

import json
import logging
import re
from typing import Annotated

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from wish_models.settings import Settings
from wish_tools.tool_step_trace import main as step_trace_main

from ..constants import DIALOG_AVOIDANCE_DOC, LIST_FILES_DOC
from ..models import GraphState

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def clean_llm_response(response_text: str) -> str:
    """LLMからの応答をクリーンアップしてJSONを抽出する

    Args:
        response_text: LLMからの応答テキスト

    Returns:
        クリーンアップされたJSON文字列
    """
    if not response_text:
        logger.error("Empty response from LLM")
        return "{}"

    # レスポンスをトリム
    cleaned_text = response_text.strip()

    # マークダウンコードブロックを処理
    if cleaned_text.startswith("```") and "```" in cleaned_text[3:]:
        # コードブロックの開始行と終了行を特定
        lines = cleaned_text.split("\n")
        start_idx = 1  # 最初の```の次の行

        # 言語指定がある場合（例: ```json）は調整
        if lines[0].startswith("```") and len(lines[0]) > 3:
            start_idx = 1

        # 終了行を見つける
        end_idx = len(lines) - 1
        for i in range(start_idx, len(lines)):
            if lines[i].strip() == "```":
                end_idx = i
                break

        # コードブロックの内容を抽出
        cleaned_text = "\n".join(lines[start_idx:end_idx])

    # JSONっぽい部分を抽出
    if not (cleaned_text.startswith("{") and cleaned_text.endswith("}")):
        json_match = re.search(r'\{.*\}', cleaned_text, re.DOTALL)
        if json_match:
            cleaned_text = json_match.group(0)
            logger.info(f"Extracted JSON from response: {cleaned_text}")
        else:
            logger.error(f"Could not extract JSON from response: {cleaned_text}")
            return "{}"

    return cleaned_text


def modify_command(state: Annotated[GraphState, "Current state"], settings_obj: Settings) -> GraphState:
    """Modify commands to avoid interactive prompts and use allowed list files.

    Args:
        state: The current graph state.

    Returns:
        Updated graph state with modified commands.
    """
    try:
        # If no command candidates, return the original state
        if not state.command_candidates:
            logger.info("No commands to modify")
            return state

        # Create the LLM
        model = settings_obj.OPENAI_MODEL or "gpt-4o"
        llm = ChatOpenAI(model=model, temperature=0.1)

        # Create the prompt for dialog avoidance
        dialog_avoidance_prompt = ChatPromptTemplate.from_template(
            """あなたは合法なペネトレーションテストに従事しているAIです。

「コマンド」と「参考ドキュメント」を受け取ります。
あなたの役割は、コマンドが対話的なものであった場合に、それを非対話的に修正することです。
参考ドキュメントに非対話的なコマンドの使い方が載っていれば、それを使用してください。

# コマンド
{command}

# 参考ドキュメント
{dialog_avoidance_doc}

出力は以下の形式の有効なJSONのみを返してください:
{{ "command": "修正後のコマンド" }}

重要:
- コードブロック記法（```）は使用しないでください
- 説明や追加のテキストは含めないでください
- 出力は必ず有効な単一のJSONオブジェクトである必要があります
- JSONオブジェクトのみを出力してください
"""
        )

        # Create the prompt for list file replacement
        list_files_prompt = ChatPromptTemplate.from_template(
            """あなたは合法なペネトレーションテストに従事しているAIです。

「コマンド」と「参考ドキュメント」を受け取ります。
あなたの役割は、コマンドに辞書攻撃用のリストファイルが含まれていた場合に、それを使用許可のあるファイルに置き換えることです。
参考ドキュメントに使用許可のあるファイルパスが載っているので、それを使用してください。

# コマンド
{command}

# 参考ドキュメント
{list_files_doc}

出力は以下の形式の有効なJSONのみを返してください:
{{ "command": "修正後のコマンド" }}

重要:
- コードブロック記法（```）は使用しないでください
- 説明や追加のテキストは含めないでください
- 出力は必ず有効な単一のJSONオブジェクトである必要があります
- JSONオブジェクトのみを出力してください
"""
        )

        # Create the output parser
        str_parser = StrOutputParser()

        # Process each command
        modified_commands = []
        for i, command in enumerate(state.command_candidates):
            # Call StepTrace if run_id is provided
            if state.run_id:
                try:
                    step_trace_main(
                        run_id=state.run_id,
                        trace_name=f"コマンド修正前_{i+1}",
                        trace_message=f"# コマンド\n{command}\n\n# タイムアウト [sec]\n30"
                    )
                except Exception as e:
                    logger.error(f"Error calling StepTrace: {e}", exc_info=True)
            # Create the chains for each command to avoid reusing the same chain
            dialog_avoidance_chain = dialog_avoidance_prompt | llm | str_parser
            list_files_chain = list_files_prompt | llm | str_parser

            # Apply dialog avoidance
            try:
                dialog_result = dialog_avoidance_chain.invoke({
                    "command": command,
                    "dialog_avoidance_doc": DIALOG_AVOIDANCE_DOC
                })

                # LLMの応答をクリーンアップ
                cleaned_dialog_result = clean_llm_response(dialog_result)

                # JSONとしてパース
                try:
                    dialog_json = json.loads(cleaned_dialog_result)
                    modified_command = dialog_json.get("command", command)
                    logger.info(f"Dialog avoidance applied: {command} -> {modified_command}")
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error in dialog avoidance: {e}, response: {cleaned_dialog_result}")
                    modified_command = command
            except Exception as e:
                logger.error(f"Error applying dialog avoidance: {e}", exc_info=True)
                modified_command = command

            # Apply list file replacement
            try:
                list_files_result = list_files_chain.invoke({
                    "command": modified_command,
                    "list_files_doc": LIST_FILES_DOC
                })

                # LLMの応答をクリーンアップ
                cleaned_list_files_result = clean_llm_response(list_files_result)

                # JSONとしてパース
                try:
                    list_files_json = json.loads(cleaned_list_files_result)
                    final_command = list_files_json.get("command", modified_command)
                    logger.info(f"List file replacement applied: {modified_command} -> {final_command}")
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error in list file replacement: {e}, response: "
                                 f"{cleaned_list_files_result}")
                    final_command = modified_command
            except Exception as e:
                logger.error(f"Error applying list file replacement: {e}", exc_info=True)
                final_command = modified_command

            # Call StepTrace for modified command if run_id is provided
            if state.run_id:
                try:
                    step_trace_main(
                        run_id=state.run_id,
                        trace_name=f"コマンド修正後_{i+1}",
                        trace_message=f"# コマンド\n{final_command}\n\n# タイムアウト [sec]\n30"
                    )
                except Exception as e:
                    logger.error(f"Error calling StepTrace: {e}", exc_info=True)

            modified_commands.append(final_command)

        # Update the state
        return GraphState(
            query=state.query,
            context=state.context,
            processed_query=state.processed_query,
            command_candidates=modified_commands,
            generated_command=state.generated_command,
            is_retry=state.is_retry,
            error_type=state.error_type,
            act_result=state.act_result
        )
    except Exception as e:
        logger.error(f"Error modifying commands: {str(e)}", exc_info=True)
        # Fail fast: エラーが発生した場合は早期に失敗を通知
        return GraphState(
            query=state.query,
            context=state.context,
            processed_query=state.processed_query,
            command_candidates=state.command_candidates,
            generated_command=None,
            api_error=True,
            error_message=f"Command modification failed: {str(e)}",
            is_retry=state.is_retry,
            error_type=state.error_type,
            act_result=state.act_result
        )
