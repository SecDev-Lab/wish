"""Models for the command generation graph."""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field
from wish_models.command_result import CommandInput
from wish_models.system_info import SystemInfo
from wish_models.wish.wish import Wish


class GraphState(BaseModel):
    """Class representing the state of LangGraph.

    This class is used to maintain state during LangGraph execution and pass data between nodes.
    wish-command-generation takes a Wish object and outputs multiple commands (CommandInput) to fulfill it.
    """

    wish: Wish
    """The Wish object to be processed. The Wish.wish field contains the natural language command request."""

    context: Dict[str, Any] = Field(default_factory=dict, description="Context for command generation")
    """Context information for command generation, such as current directory, history, etc."""

    query: str | None = None
    """Query for RAG search. Used to search for relevant documents in the RAG system."""

    command_inputs: list[CommandInput] = Field(default_factory=list)
    """List of generated command inputs. This is the final output of the graph."""

    error: Optional[str] = None
    """Error message if command generation fails. None if successful."""

    system_info: SystemInfo | None = None
    """System information for command generation."""
