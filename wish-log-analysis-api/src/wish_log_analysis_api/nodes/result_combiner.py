"""Result combiner node functions for the log analysis graph."""


from wish_models.command_result import CommandResult
from wish_models.command_result.command_state import CommandState

from ..models import GraphState


def combine_results(state: GraphState) -> GraphState:
    """Combine the results from log summarization and command state classifier.

    Args:
        state: The current graph state.

    Returns:
        Updated graph state with analyzed command result.
    """
    # Create a new state object
    new_state = GraphState(
        command_result=state.command_result,
        log_summary=state.log_summary,
        command_state=state.command_state,
        api_error=state.api_error
    )

    # Check if log_summary and command_state are both set
    if state.log_summary is None or state.command_state is None:
        # If there was an API error, we can still proceed with what we have
        if not state.api_error:
            import logging
            logging.error("Missing required fields in state: log_summary or command_state is None")
            logging.error(f"log_summary: {state.log_summary}")
            logging.error(f"command_state: {state.command_state}")
            logging.error(f"api_error: {state.api_error}")
            raise ValueError("log_summary and command_state must be set")

    # If there was an API error, ensure the command state is set to API_ERROR
    command_state = state.command_state
    if state.api_error and command_state != CommandState.API_ERROR:
        command_state = CommandState.API_ERROR

    # Create the analyzed command result
    analyzed_command_result = CommandResult(
        num=state.command_result.num,
        command=state.command_result.command,
        exit_code=state.command_result.exit_code,
        log_files=state.command_result.log_files,
        log_summary=state.log_summary or "Error: Unable to generate log summary due to API error",
        state=command_state or CommandState.API_ERROR,
        created_at=state.command_result.created_at,
        finished_at=state.command_result.finished_at
    )

    # Set the analyzed command result in the new state
    new_state.analyzed_command_result = analyzed_command_result

    # Return the new state
    return new_state
