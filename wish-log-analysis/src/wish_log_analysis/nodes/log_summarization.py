"""Log summarization node functions for the log analysis graph."""

import os

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from ..models import GraphState
from ..settings import settings

# Define the prompt template
LOG_SUMMARIZATION_PROMPT = """
You are tasked with receiving a shell command and its execution results (exit_code, stdout, stderr)
and summarizing the results.
The summary will be passed to an LLM with a limited context window, so it needs to be as concise as possible.

Please follow these steps to complete the task:

1. Check the exit_code. The summarization method differs between exit_code 0 and non-zero.

2. If the exit_code is 0, summarize as concisely as possible while retaining all information needed
   to understand what to do next for penetration testing.
   Examples of important information that must be retained include:
   - IP addresses
   - Port numbers
   - File paths
   - Usernames
   - Version information
   - Vulnerability/misconfiguration items

3. If the exit_code is non-zero, concisely summarize the reason for the command failure.

4. Only include the summary in your output.

# Command
{command}

# exit_code
{exit_code}

# stdout
{stdout}

# stderr
{stderr}
"""


def summarize_log(state: GraphState) -> GraphState:
    """Summarize the log from a command result.

    Args:
        state: The current graph state.

    Returns:
        Updated graph state with log summary.
    """
    # Create a new state object to avoid modifying the original
    # Only set the fields this node is responsible for
    new_state = GraphState(
        command_result=state.command_result,
        command_state=state.command_state,
        analyzed_command_result=state.analyzed_command_result,
        api_error=state.api_error,
    )

    # Get the command and exit code from the state
    command = state.command_result.command
    exit_code = state.command_result.exit_code

    # Read stdout and stderr from log_files
    stdout = ""
    stderr = ""
    if state.command_result.log_files:
        if state.command_result.log_files.stdout and os.path.exists(state.command_result.log_files.stdout):
            with open(state.command_result.log_files.stdout, "r", encoding="utf-8") as f:
                stdout = f.read()
        if state.command_result.log_files.stderr and os.path.exists(state.command_result.log_files.stderr):
            with open(state.command_result.log_files.stderr, "r", encoding="utf-8") as f:
                stderr = f.read()

    # Create the prompt
    prompt = PromptTemplate.from_template(LOG_SUMMARIZATION_PROMPT)

    # Initialize the OpenAI model
    model = ChatOpenAI(model=settings.OPENAI_MODEL, api_key=settings.OPENAI_API_KEY)

    # Create the chain
    chain = prompt | model | StrOutputParser()

    # Generate the summary
    try:
        summary = chain.invoke({"command": command, "exit_code": exit_code, "stdout": stdout, "stderr": stderr})

        # Set the log summary in the new state
        new_state.log_summary = summary

    except Exception as e:
        # In case of any error, provide a fallback summary and log the error
        error_message = f"Error generating summary: {str(e)}"

        # Log the error
        import logging

        logging.error(error_message)
        logging.error(f"Command: {command}")
        logging.error(f"Exit code: {exit_code}")

        # Set error information in the new state
        new_state.log_summary = error_message
        new_state.api_error = True

    # Return the new state
    return new_state
