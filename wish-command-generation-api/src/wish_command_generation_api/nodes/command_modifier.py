"""Command modifier node for the command generation graph."""

import json
import logging
from typing import Annotated

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from wish_models.settings import Settings

from ..constants import DIALOG_AVOIDANCE_DOC, LIST_FILES_DOC
from ..models import GraphState

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


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

出力は以下の形式のJSONで返してください:
{{ "command": "修正後のコマンド" }}

JSONのみを出力してください。説明や追加のテキストは含めないでください。
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

出力は以下の形式のJSONで返してください:
{{ "command": "修正後のコマンド" }}

JSONのみを出力してください。説明や追加のテキストは含めないでください。
"""
        )

        # Create the output parser
        str_parser = StrOutputParser()

        # Process each command
        modified_commands = []
        for command in state.command_candidates:
            # Create the chains for each command to avoid reusing the same chain
            dialog_avoidance_chain = dialog_avoidance_prompt | llm | str_parser
            list_files_chain = list_files_prompt | llm | str_parser

            # Apply dialog avoidance
            try:
                dialog_result = dialog_avoidance_chain.invoke({
                    "command": command,
                    "dialog_avoidance_doc": DIALOG_AVOIDANCE_DOC
                })
                dialog_json = json.loads(dialog_result)
                modified_command = dialog_json.get("command", command)
                logger.info(f"Dialog avoidance applied: {command} -> {modified_command}")
            except Exception as e:
                logger.exception(f"Error applying dialog avoidance: {e}")
                modified_command = command

            # Apply list file replacement
            try:
                list_files_result = list_files_chain.invoke({
                    "command": modified_command,
                    "list_files_doc": LIST_FILES_DOC
                })
                list_files_json = json.loads(list_files_result)
                final_command = list_files_json.get("command", modified_command)
                logger.info(f"List file replacement applied: {modified_command} -> {final_command}")
            except Exception as e:
                logger.exception(f"Error applying list file replacement: {e}")
                final_command = modified_command

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
    except Exception:
        logger.exception("Error modifying commands")
        # Return the original state
        return state
