"""Feedback analyzer node for the command generation graph."""

import logging
from typing import Annotated

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
    try:
        # If no act_result, this is the first execution
        if not state.act_result:
            logger.info("No feedback provided, this is the first execution")
            return GraphState(
                query=state.query,
                context=state.context,
                processed_query=state.processed_query,
                command_candidates=state.command_candidates,
                generated_command=state.generated_command,
                is_retry=False,
                error_type=None,
                act_result=None
            )

        # Analyze feedback to determine error type
        error_type = None
        for result in state.act_result:
            if result.exit_class == "TIMEOUT":
                error_type = "TIMEOUT"
                logger.info(f"Detected TIMEOUT error in command: {result.command}")
                break
            elif result.exit_class == "NETWORK_ERROR":
                error_type = "NETWORK_ERROR"
                logger.info(f"Detected NETWORK_ERROR in command: {result.command}")
                break

        # Update the state
        return GraphState(
            query=state.query,
            context=state.context,
            processed_query=state.processed_query,
            command_candidates=state.command_candidates,
            generated_command=state.generated_command,
            is_retry=True,
            error_type=error_type,
            act_result=state.act_result
        )
    except Exception as e:
        logger.exception("Error analyzing feedback")
        # Return the original state with error flag
        return GraphState(
            query=state.query,
            context=state.context,
            processed_query=state.processed_query,
            command_candidates=state.command_candidates,
            generated_command=state.generated_command,
            is_retry=False,
            error_type=None,
            act_result=state.act_result,
            api_error=True
        )
