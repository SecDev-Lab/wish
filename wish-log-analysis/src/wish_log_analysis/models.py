"""Models for the log analysis graph."""

from pydantic import BaseModel, Field
from wish_models.command_result import CommandResult
from wish_models.command_result.command_state import CommandState


class GraphState(BaseModel):
    """Class representing the state of LangGraph.

    This class is used to maintain state during LangGraph execution and pass data between nodes.
    wish-log-analysis takes a CommandResult object with None fields and outputs a CommandResult
    with all fields filled.
    """

    command_result: CommandResult
    """The CommandResult object to be processed. May have None fields for stdout, stderr."""

    log_summary: str | None = None
    """Summary of the log. Used to improve readability of the command result."""

    command_state: CommandState | None = None
    """Classification of the command result (SUCCESS, COMMAND_NOT_FOUND, etc.)."""

    analyzed_command_result: CommandResult | None = None
    """The final CommandResult object with all fields filled. This is the output of the graph."""
