"""Result formatter node for the command generation graph."""

import logging
from typing import Annotated

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from wish_models.settings import Settings

from ..models import GeneratedCommand, GraphState

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Define the prompt template
RESULT_FORMATTER_PROMPT = """You are an expert in explaining shell commands.
Your task is to provide a clear explanation for the generated shell command.

Generated Command: {command}

Original User Query: {original_query}

Instructions:
1. Explain what the command does in simple terms
2. Explain why this command is appropriate for the user's query
3. Mention any important flags or options used in the command
4. Keep the explanation concise but informative

Output only the explanation for the command.
"""


def format_result(state: Annotated[GraphState, "Current state"], settings_obj: Settings) -> GraphState:
    """Format the result with explanation.

    Args:
        state: The current graph state.

    Returns:
        Updated graph state with formatted result.
    """
    try:
        # Extract query and command candidates
        original_query = state.query
        if not state.command_candidates:
            # エラーを発生させる（コマンド候補が必須）
            raise ValueError("No command candidates available")

        # Create the LLM
        model = settings_obj.OPENAI_MODEL or "gpt-4o"
        llm = ChatOpenAI(model=model, temperature=0.1)

        # Create the prompt
        prompt = ChatPromptTemplate.from_template(RESULT_FORMATTER_PROMPT)

        # 各コマンドに説明を追加
        generated_commands = []
        for cmd_input in state.command_candidates:
            command = cmd_input.command

            # タイムアウト値が設定されていることを確認
            assert cmd_input.timeout_sec is not None, f"タイムアウト値が設定されていません: {command}"

            # Create the chain
            chain = prompt | llm

            # Invoke the chain
            result = chain.invoke({
                "command": command,
                "original_query": original_query
            })

            # Extract the explanation
            explanation = result.content.strip()
            logger.info(f"Generated explanation for command {command}: {explanation}")

            # Create the generated command object
            generated_command = GeneratedCommand.from_command_input(
                command_input=cmd_input,
                explanation=explanation
            )
            generated_commands.append(generated_command)

        # Update the state
        return GraphState(
            query=state.query,
            context=state.context,
            processed_query=state.processed_query,
            command_candidates=state.command_candidates,
            generated_commands=generated_commands
        )
    except Exception as e:
        raise RuntimeError("Error formatting result") from e
