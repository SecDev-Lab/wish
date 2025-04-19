"""Main graph definition for the command generation system."""

from langgraph.graph import END, START, StateGraph
from wish_models.settings import Settings

from .models import GraphState
from .nodes import command_generation, rag


def create_command_generation_graph(settings_obj: Settings, compile: bool = True) -> StateGraph:
    """Create a command generation graph

    Args:
        settings_obj: Settings object to use.
        compile: If True, returns a compiled graph. If False, returns a pre-compiled graph.

    Returns:
        Compiled or pre-compiled graph object
    """

    # Log LangSmith configuration if tracing is enabled
    if settings_obj.LANGCHAIN_TRACING_V2:
        import logging
        logging.info(f"LangSmith tracing enabled for project: {settings_obj.LANGCHAIN_PROJECT}")

    # Create the graph
    graph = StateGraph(GraphState)

    # Add nodes
    graph.add_node("query_generation", lambda state: rag.generate_query(state, settings_obj))
    graph.add_node("retrieve_documents", lambda state: rag.retrieve_documents(state, settings_obj))
    graph.add_node("generate_commands", lambda state: command_generation.generate_commands(state, settings_obj))

    # Add edges (linear graph)
    graph.add_edge(START, "query_generation")
    graph.add_edge("query_generation", "retrieve_documents")
    graph.add_edge("retrieve_documents", "generate_commands")
    graph.add_edge("generate_commands", END)

    # Whether to compile or not
    if compile:
        return graph.compile()
    return graph
