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
        command_candidates = state.command_candidates or ["echo 'No command generated'"]

        # Use the first command candidate
        command = command_candidates[0]

        # Create the LLM
        model = settings_obj.OPENAI_MODEL or "gpt-4o"
        llm = ChatOpenAI(model=model, temperature=0.1)

        # Create the prompt
        prompt = ChatPromptTemplate.from_template(RESULT_FORMATTER_PROMPT)

        # Create the chain
        chain = prompt | llm

        # Invoke the chain
        result = chain.invoke({
            "command": command,
            "original_query": original_query
        })

        # Extract the explanation
        explanation = result.content.strip()
        logger.info(f"Generated explanation: {explanation}")

        # Create the generated command object
        generated_command = GeneratedCommand(
            command=command,
            explanation=explanation
        )

        # Update the state
        return GraphState(
            query=state.query,
            context=state.context,
            processed_query=state.processed_query,
            command_candidates=state.command_candidates,
            generated_command=generated_command
        )
    except Exception as e:
        logger.exception("Error formatting result")
        # Return the original state with a fallback generated command
        command = state.command_candidates[0] if state.command_candidates else "echo 'Command generation failed'"

        fallback_command = GeneratedCommand(
            command=command,
            explanation=f"Error: Failed to generate explanation due to {str(e)}"
        )

        return GraphState(
            query=state.query,
            context=state.context,
            processed_query=state.processed_query,
            command_candidates=state.command_candidates,
            generated_command=fallback_command,
            api_error=True
        )
