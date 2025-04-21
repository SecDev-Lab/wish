"""Command generator node for the command generation graph."""

import logging
from typing import Annotated

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from wish_models.settings import Settings

from ..constants import DIALOG_AVOIDANCE_DOC, DIVIDE_AND_CONQUER_DOC, FAST_ALTERNATIVE_DOC, LIST_FILES_DOC
from ..models import GraphState

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Define the prompt template
COMMAND_GENERATOR_PROMPT = """You are an expert in shell command generation.
Your task is to generate the most appropriate shell command based on the user's query.

Processed Query: {processed_query}

Original Query: {original_query}

Context Information:
- Current Directory: {current_directory}
- Command History: {command_history}

Instructions:
1. Generate a shell command that best addresses the user's query
2. Consider the current directory and command history for context
3. Use standard shell syntax (bash/zsh)
4. Prioritize common utilities and avoid complex one-liners unless necessary
5. Generate only the command, no explanation
6. Follow the guidelines in the documentation below for specific scenarios

# 対話回避ガイドライン
{dialog_avoidance_doc}

# 高速な代替コマンドガイドライン
{fast_alternative_doc}

# リストファイルガイドライン
{list_files_doc}

# 分割統治ガイドライン
{divide_and_conquer_doc}

Output only the shell command that should be executed.
"""


def generate_command(state: Annotated[GraphState, "Current state"], settings_obj: Settings) -> GraphState:
    """Generate a shell command based on the processed query.

    Args:
        state: The current graph state.

    Returns:
        Updated graph state with command candidates.
    """
    try:
        # Extract query and context
        original_query = state.query
        processed_query = state.processed_query or original_query  # Fallback to original if processed is None
        context = state.context

        # Extract specific context elements with defaults
        current_directory = context.get("current_directory", "unknown")
        command_history = context.get("history", [])
        command_history_str = "\n".join(command_history) if command_history else "No command history available"

        # Create the LLM
        model = settings_obj.OPENAI_MODEL or "gpt-4o"
        llm = ChatOpenAI(model=model, temperature=0.2)

        # Create the prompt
        prompt = ChatPromptTemplate.from_template(COMMAND_GENERATOR_PROMPT)

        # Create the chain
        chain = prompt | llm

        # Invoke the chain
        result = chain.invoke({
            "processed_query": processed_query,
            "original_query": original_query,
            "current_directory": current_directory,
            "command_history": command_history_str,
            "dialog_avoidance_doc": DIALOG_AVOIDANCE_DOC,
            "fast_alternative_doc": FAST_ALTERNATIVE_DOC,
            "list_files_doc": LIST_FILES_DOC,
            "divide_and_conquer_doc": DIVIDE_AND_CONQUER_DOC
        })

        # Extract the generated command and remove Markdown code block formatting if present
        command = result.content.strip()

        # Remove Markdown code block formatting if present
        if command.startswith("```"):
            # Extract the command from the code block
            lines = command.split("\n")
            # Remove the first line (```bash or similar)
            lines = lines[1:]
            # Remove the last line if it's a closing ```
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            # Join the remaining lines
            command = "\n".join(lines).strip()

        logger.info(f"Generated command: {command}")

        # Generate a list of command candidates (in this case, just one)
        command_candidates = [command]

        # Update the state
        return GraphState(
            query=state.query,
            context=state.context,
            processed_query=state.processed_query,
            command_candidates=command_candidates,
            is_retry=state.is_retry,
            error_type=state.error_type,
            act_result=state.act_result
        )
    except Exception:
        logger.exception("Error generating command")
        # Return the original state with a fallback command
        return GraphState(
            query=state.query,
            context=state.context,
            processed_query=state.processed_query,
            command_candidates=["echo 'Command generation failed'"],
            api_error=True,
            is_retry=state.is_retry,
            error_type=state.error_type,
            act_result=state.act_result
        )
