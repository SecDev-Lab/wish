"""Command generator node for the command generation graph."""

import logging
from typing import Annotated

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from wish_models import settings

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

Output only the shell command that should be executed.
"""


def generate_command(state: Annotated[GraphState, "Current state"]) -> GraphState:
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
        model = settings.OPENAI_MODEL or "gpt-4o"
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
            "command_history": command_history_str
        })

        # Extract the generated command
        command = result.content.strip()
        logger.info(f"Generated command: {command}")

        # Generate a list of command candidates (in this case, just one)
        command_candidates = [command]

        # Update the state
        return GraphState(
            query=state.query,
            context=state.context,
            processed_query=state.processed_query,
            command_candidates=command_candidates
        )
    except Exception:
        logger.exception("Error generating command")
        # Return the original state with a fallback command
        return GraphState(
            query=state.query,
            context=state.context,
            processed_query=state.processed_query,
            command_candidates=["echo 'Command generation failed'"],
            api_error=True
        )
