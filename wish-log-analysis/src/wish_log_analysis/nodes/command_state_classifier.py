"""Command state classifier node functions for the log analysis graph."""

import os

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from wish_models.command_result.command_state import CommandState

from ..models import GraphState
from ..settings import settings

# Define the prompt template
COMMAND_STATE_CLASSIFIER_PROMPT = """
As a system operations analyst, your role is to analyze command outputs and report the results.
Follow these specific steps:

1. If the `exit_code` is "0", output "SUCCESS" and end.
2. Otherwise, check the command output from `stdout` and `stderr`.
3. Choose the appropriate error code from the following:
   - COMMAND_NOT_FOUND: When the command is not found on the local machine
   - FILE_NOT_FOUND: When a local file referenced in the command is not found (excluding remote files like smb)
   - REMOTE_OPERATION_FAILED: When an operation on a remote machine (e.g., file reference, command execution) fails
   - TIMEOUT: When command execution times out
   - NETWORK_ERROR: When a network error occurs
   - OTHERS: When an error not listed above occurs
4. Output the selected error code and end.

# command
{command}

# exit_code
{exit_code}

# stdout
{stdout}

# stderr
{stderr}
"""


def classify_command_state(state: GraphState) -> GraphState:
    """Classify the command state from a command result.

    Args:
        state: The current graph state.

    Returns:
        Updated graph state with command state.
    """
    # Create a new state object to avoid modifying the original
    # Only set the fields this node is responsible for
    new_state = GraphState(
        command_result=state.command_result,
        log_summary=state.log_summary,
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
    prompt = PromptTemplate.from_template(COMMAND_STATE_CLASSIFIER_PROMPT)

    # Initialize the OpenAI model
    model = ChatOpenAI(model=settings.OPENAI_MODEL, api_key=settings.OPENAI_API_KEY)

    # Create the chain
    chain = prompt | model | StrOutputParser()

    # Generate the classification
    try:
        classification_str = chain.invoke(
            {"command": command, "exit_code": exit_code, "stdout": stdout, "stderr": stderr}
        ).strip()

        # Convert the classification string to CommandState
        if classification_str == "SUCCESS":
            command_state = CommandState.SUCCESS
        elif classification_str == "COMMAND_NOT_FOUND":
            command_state = CommandState.COMMAND_NOT_FOUND
        elif classification_str == "FILE_NOT_FOUND":
            command_state = CommandState.FILE_NOT_FOUND
        elif classification_str == "REMOTE_OPERATION_FAILED":
            command_state = CommandState.REMOTE_OPERATION_FAILED
        elif classification_str == "TIMEOUT":
            command_state = CommandState.TIMEOUT
        elif classification_str == "NETWORK_ERROR":
            command_state = CommandState.NETWORK_ERROR
        else:
            command_state = CommandState.OTHERS

        # Set the command state in the new state
        new_state.command_state = command_state

    except Exception as e:
        # In case of any error, log it and set API_ERROR state
        error_message = f"Error classifying command state: {str(e)}"

        # Log the error
        import logging

        logging.error(error_message)
        logging.error(f"Command: {command}")
        logging.error(f"Exit code: {exit_code}")

        # Set error information in the new state
        new_state.command_state = CommandState.API_ERROR
        new_state.api_error = True

    # Return the new state
    return new_state
