"""Feedback analyzer node for the command generation graph."""

import logging
from typing import Annotated

from wish_models.command_result import CommandState
from wish_models.settings import Settings

from ..models import GraphState

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def analyze_feedback(state: Annotated[GraphState, "Current state"], settings_obj: Settings) -> GraphState:
    """Analyze feedback and determine error type.

    Args:
        state: The current graph state.

    Returns:
        Updated graph state with error type.
    """
    # If no act_result, this is the first execution
    if not state.failed_command_results:
        logger.info("No feedback provided, this is the first execution")
        return GraphState(
            query=state.query,
            context=state.context,
            processed_query=state.processed_query,
            command_candidates=state.command_candidates,
            generated_commands=state.generated_commands,
            is_retry=False,
            error_type=None,
            failed_command_results=None
        )

    # Analyze feedback to determine error type
    error_type = None
    has_timeout = False
    has_network_error = False
    has_other_error = False

    # First pass: check for all error types
    for result in state.failed_command_results:
        if result.state == CommandState.TIMEOUT:
            has_timeout = True
            logger.info(f"Detected TIMEOUT error in command: {result.command}")
        elif result.state == CommandState.NETWORK_ERROR:
            has_network_error = True
            logger.info(f"Detected NETWORK_ERROR in command: {result.command}")
        elif result.state == CommandState.OTHERS:
            has_other_error = True
            logger.info(f"Detected OTHER error in command: {result.command}")

    # Prioritize TIMEOUT over NETWORK_ERROR
    if has_timeout:
        error_type = "TIMEOUT"
        is_retry = True
    elif has_network_error:
        error_type = "NETWORK_ERROR"
        is_retry = True
    elif has_other_error:
        error_type = "OTHERS"
        is_retry = False  # Don't retry for unknown errors
    else:
        is_retry = False

    # Update the state
    return GraphState(
        query=state.query,
        context=state.context,
        processed_query=state.processed_query,
        command_candidates=state.command_candidates,
        generated_commands=state.generated_commands,
        is_retry=is_retry,
        error_type=error_type,
        failed_command_results=state.failed_command_results
    )
