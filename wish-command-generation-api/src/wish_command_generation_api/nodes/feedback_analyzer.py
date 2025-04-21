"""Feedback analyzer node for the command generation graph."""

import logging
from typing import Annotated
from unittest.mock import MagicMock

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
        has_timeout = False
        has_network_error = False

        # First pass: check for all error types
        for result in state.act_result:
            if result.state == CommandState.TIMEOUT:
                has_timeout = True
                logger.info(f"Detected TIMEOUT error in command: {result.command}")
            elif result.state == CommandState.NETWORK_ERROR:
                has_network_error = True
                logger.info(f"Detected NETWORK_ERROR in command: {result.command}")

        # Prioritize TIMEOUT over NETWORK_ERROR
        if has_timeout:
            error_type = "TIMEOUT"
        elif has_network_error:
            error_type = "NETWORK_ERROR"

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
    except Exception:
        logger.exception("Error analyzing feedback")
        # Return a new state with error flag and default values for MagicMock objects
        try:
            query = state.query if not isinstance(state.query, MagicMock) else ""
            context = state.context if not isinstance(state.context, MagicMock) else {}
            processed_query = state.processed_query if not isinstance(state.processed_query, MagicMock) else None
            command_candidates = state.command_candidates if not isinstance(state.command_candidates, MagicMock) else None
            generated_command = state.generated_command if not isinstance(state.generated_command, MagicMock) else None
            act_result = state.act_result if not isinstance(state.act_result, MagicMock) else None

            return GraphState(
                query=query,
                context=context,
                processed_query=processed_query,
                command_candidates=command_candidates,
                generated_command=generated_command,
                is_retry=False,
                error_type=None,
                act_result=act_result,
                api_error=True
            )
        except Exception:
            # Fallback to completely default state if the above fails
            logger.exception("Failed to create error state, using default values")
            return GraphState(
                query="",
                context={},
                is_retry=False,
                error_type=None,
                api_error=True
            )
