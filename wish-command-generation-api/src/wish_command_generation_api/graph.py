"""Main graph definition for the command generation system."""

from typing import Optional

from langgraph.graph import END, START, StateGraph
from wish_models import settings

from .config import GeneratorConfig
from .models import GraphState
from .nodes import command_generator, query_processor, result_formatter


def create_command_generation_graph(config: Optional[GeneratorConfig] = None, compile: bool = True) -> StateGraph:
    """Create a command generation graph

    Args:
        config: Configuration object (if None, load from environment variables)
        compile: If True, returns a compiled graph. If False, returns a pre-compiled graph.

    Returns:
        Compiled or pre-compiled graph object
    """
    # Load from environment variables if no config is provided
    if config is None:
        config = GeneratorConfig.from_env()

    # Apply configuration
    import os
    os.environ["OPENAI_API_KEY"] = config.openai_api_key
    os.environ["OPENAI_MODEL"] = config.openai_model
    os.environ["LANGCHAIN_PROJECT"] = config.langchain_project
    os.environ["LANGCHAIN_TRACING_V2"] = str(config.langchain_tracing_v2).lower()

    # Set project name
    settings.LANGCHAIN_PROJECT = config.langchain_project

    # Log LangSmith configuration if tracing is enabled
    if config.langchain_tracing_v2:
        import logging
        logging.info(f"LangSmith tracing enabled for project: {settings.LANGCHAIN_PROJECT}")

    # Create the graph
    graph = StateGraph(GraphState)

    # Add nodes
    graph.add_node("query_processor", query_processor.process_query)
    graph.add_node("command_generator", command_generator.generate_command)
    graph.add_node("result_formatter", result_formatter.format_result)

    # Add edges for serial execution
    graph.add_edge(START, "query_processor")
    graph.add_edge("query_processor", "command_generator")
    graph.add_edge("command_generator", "result_formatter")
    graph.add_edge("result_formatter", END)

    # Whether to compile or not
    if compile:
        return graph.compile()
    return graph
