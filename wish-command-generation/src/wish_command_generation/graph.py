"""Main graph definition for the command generation system."""

from langgraph.graph import StateGraph, END, START

from wish_models.command_result import CommandInput
from wish_models.wish.wish import Wish

from .models import GraphState
from .nodes import command_generation, rag


def create_command_generation_graph(compile: bool = True) -> StateGraph:
    """Create a command generation graph
    
    Args:
        compile: If True, returns a compiled graph. If False, returns a pre-compiled graph.
    
    Returns:
        Compiled or pre-compiled graph object
    """
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
