"""Main graph definition for the log analysis system."""

from langgraph.graph import END, START, StateGraph
from wish_models import settings

from .models import GraphState
from .nodes import command_state_classifier, log_summarization, result_combiner


def create_log_analysis_graph(compile: bool = True) -> StateGraph:
    """Create a log analysis graph

    Args:
        compile: If True, returns a compiled graph. If False, returns a pre-compiled graph.

    Returns:
        Compiled or pre-compiled graph object
    """
    # Set project name
    settings.LANGCHAIN_PROJECT = "wish-log-analysis"

    # Log LangSmith configuration if tracing is enabled
    if settings.LANGCHAIN_TRACING_V2:
        import logging
        logging.info(f"LangSmith tracing enabled for project: {settings.LANGCHAIN_PROJECT}")

    # Create the graph
    graph = StateGraph(GraphState)

    # Add nodes
    graph.add_node("log_summarization", log_summarization.summarize_log)
    graph.add_node("command_state_classifier", command_state_classifier.classify_command_state)
    graph.add_node("result_combiner", result_combiner.combine_results)

    # Add edges for serial execution
    graph.add_edge(START, "log_summarization")
    graph.add_edge("log_summarization", "command_state_classifier")
    graph.add_edge("command_state_classifier", "result_combiner")
    graph.add_edge("result_combiner", END)

    # Whether to compile or not
    if compile:
        return graph.compile()
    return graph
