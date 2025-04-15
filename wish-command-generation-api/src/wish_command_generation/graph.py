"""Main graph definition for the command generation system."""

from langgraph.graph import END, START, StateGraph
from wish_models import settings

from .models import GraphState
from .nodes import command_generation, rag


def create_command_generation_graph(compile: bool = True) -> StateGraph:
    """Create a command generation graph

    Args:
        compile: If True, returns a compiled graph. If False, returns a pre-compiled graph.

    Returns:
        Compiled or pre-compiled graph object
    """
    # Set project name
    settings.LANGCHAIN_PROJECT = "wish-command-generation"

    # Log LangSmith configuration if tracing is enabled
    if settings.LANGCHAIN_TRACING_V2:
        import logging
        logging.info(f"LangSmith tracing enabled for project: {settings.LANGCHAIN_PROJECT}")

    # Create the graph
    graph = StateGraph(GraphState)

    # Add nodes
    graph.add_node("query_generation", rag.generate_query)
    graph.add_node("retrieve_documents", rag.retrieve_documents)
    graph.add_node("generate_commands", command_generation.generate_commands)

    # Add edges (linear graph)
    graph.add_edge(START, "query_generation")
    graph.add_edge("query_generation", "retrieve_documents")
    graph.add_edge("retrieve_documents", "generate_commands")
    graph.add_edge("generate_commands", END)

    # Whether to compile or not
    if compile:
        return graph.compile()
    return graph
