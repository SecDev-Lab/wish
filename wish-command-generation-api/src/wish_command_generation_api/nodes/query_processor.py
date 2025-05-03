"""Query processor node for the command generation graph."""

import logging
from typing import Annotated

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from wish_models.settings import Settings

from ..models import GraphState

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Define the prompt template
QUERY_PROCESSOR_PROMPT = """You are an expert in processing user queries for shell command generation.
Your task is to normalize and enhance the user's query to make it more suitable for command generation.

User Query: {query}

Context Information:
- Current Directory: {current_directory}
- Command History: {command_history}

Instructions:
1. Understand the user's intent from the query
2. Normalize the query to remove ambiguities
3. Add any relevant context from the provided information
4. Format the query to be clear and specific

Output the processed query that will be used for command generation.
"""


def process_query(state: Annotated[GraphState, "Current state"], settings_obj: Settings) -> GraphState:
    """Process and normalize the user query.

    Args:
        state: The current graph state.

    Returns:
        Updated graph state with processed query.
    """
    try:
        # Extract query and context
        query = state.query
        context = state.context

        # Extract specific context elements with defaults
        current_directory = context.get("current_directory", "unknown")
        command_history = context.get("history", [])
        command_history_str = "\n".join(command_history) if command_history else "No command history available"

        # Create the LLM
        model = settings_obj.OPENAI_MODEL or "gpt-4o"
        llm = ChatOpenAI(model=model, temperature=0.1)

        # Create the prompt
        prompt = ChatPromptTemplate.from_template(QUERY_PROCESSOR_PROMPT)

        # Create the chain
        chain = prompt | llm

        # Invoke the chain
        result = chain.invoke({
            "query": query,
            "current_directory": current_directory,
            "command_history": command_history_str
        })

        # Extract the processed query
        processed_query = result.content.strip()
        logger.info(f"Processed query: {processed_query}")

        # Update the state
        return GraphState(
            query=state.query,
            context=state.context,
            processed_query=processed_query
        )
    except Exception:
        logger.exception("Error processing query")
        # Return the original state with the original query as processed query
        return GraphState(
            query=state.query,
            context=state.context,
            processed_query=state.query,  # Fallback to original query
            api_error=True
        )
