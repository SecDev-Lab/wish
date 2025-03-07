"""Result combiner node functions for the log analysis graph."""

import os

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
    # Check if log_summary and command_state are both set
    if state.log_summary is None or state.command_state is None:
        raise ValueError("log_summary and command_state must be set")

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

    # Create the analyzed command result
    analyzed_command_result = CommandResult(
        num=state.command_result.num,
        command=state.command_result.command,
        exit_code=state.command_result.exit_code,
        log_files=state.command_result.log_files,
        log_summary=state.log_summary,
        state=state.command_state,
        created_at=state.command_result.created_at
    )

    # Update the state
    state_dict = state.model_dump()
    state_dict["analyzed_command_result"] = analyzed_command_result

    return GraphState(**state_dict)
