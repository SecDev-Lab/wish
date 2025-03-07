"""Models for the command generation graph."""

from typing import Optional

from pydantic import BaseModel, Field
from wish_models.command_result import CommandInput
from wish_models.wish.wish import Wish


class GraphState(BaseModel):
    """Class representing the state of LangGraph.

    This class is used to maintain state during LangGraph execution and pass data between nodes.
    wish-command-generation takes a Wish object and outputs multiple commands (CommandInput) to fulfill it.
    """

    wish: Wish
    """The Wish object to be processed. The Wish.wish field contains the natural language command request."""

    context: list[str] | None = None
    """List of reference documents retrieved from RAG. Used to improve command generation accuracy."""

    query: str | None = None
    """Query for RAG search. Used to search for relevant documents in the RAG system."""

    command_inputs: list[CommandInput] = Field(default_factory=list)
    """List of generated command inputs. This is the final output of the graph."""

    error: Optional[str] = None
    """Error message if command generation fails. None if successful."""
