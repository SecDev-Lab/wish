"""Main graph definition for the log analysis system."""

from typing import Optional

from langgraph.graph import END, START, StateGraph
from wish_models.settings import Settings

from .config import AnalyzerConfig
from .models import GraphState
from .nodes import command_state_classifier, log_summarization, result_combiner


def create_log_analysis_graph(
    settings_obj: Settings,
    config: Optional[AnalyzerConfig] = None,
    compile: bool = True
) -> StateGraph:
    """Create a log analysis graph

    Args:
        config: Configuration object (if None, load from environment variables)
        compile: If True, returns a compiled graph. If False, returns a pre-compiled graph.

    Returns:
        Compiled or pre-compiled graph object
    """
    # Load from environment variables if no config is provided
    if config is None:
        config = AnalyzerConfig.from_env()

    # Apply configuration
    import os
    os.environ["OPENAI_API_KEY"] = config.openai_api_key
    os.environ["OPENAI_MODEL"] = config.openai_model
    os.environ["LANGCHAIN_PROJECT"] = config.langchain_project
    os.environ["LANGCHAIN_TRACING_V2"] = str(config.langchain_tracing_v2).lower()

    # Set project name
    settings_obj.LANGCHAIN_PROJECT = config.langchain_project

    # Log LangSmith configuration if tracing is enabled
    if config.langchain_tracing_v2:
        import logging
        logging.info(f"LangSmith tracing enabled for project: {settings_obj.LANGCHAIN_PROJECT}")

    # Create the graph
    graph = StateGraph(GraphState)

    # Add nodes
    graph.add_node(
        "log_summarization",
        lambda state: log_summarization.summarize_log(state, settings_obj)
    )
    graph.add_node(
        "command_state_classifier",
        lambda state: command_state_classifier.classify_command_state(state, settings_obj)
    )
    graph.add_node(
        "result_combiner",
        lambda state: result_combiner.combine_results(state, settings_obj)
    )

    # Add edges for serial execution
    graph.add_edge(START, "log_summarization")
    graph.add_edge("log_summarization", "command_state_classifier")
    graph.add_edge("command_state_classifier", "result_combiner")
    graph.add_edge("result_combiner", END)

    # Whether to compile or not
    if compile:
        return graph.compile()
    return graph
