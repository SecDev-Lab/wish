"""Main graph definition for the command generation system."""

from typing import Optional

from langgraph.graph import END, START, StateGraph
from wish_models.settings import Settings

from .config import GeneratorConfig
from .models import GraphState
from .nodes import (
    command_generator,
    command_modifier,
    feedback_analyzer,
    network_error_handler,
    query_processor,
    result_formatter,
    timeout_handler,
)


def create_command_generation_graph(
    settings_obj: Settings,
    config: Optional[GeneratorConfig] = None,
    compile: bool = True
) -> StateGraph:
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
    settings_obj.LANGCHAIN_PROJECT = config.langchain_project

    # Log LangSmith configuration if tracing is enabled
    if config.langchain_tracing_v2:
        import logging
        logging.info(f"LangSmith tracing enabled for project: {settings_obj.LANGCHAIN_PROJECT}")

    # Create the graph
    graph = StateGraph(GraphState)

    # Add nodes
    graph.add_node("feedback_analyzer", lambda state: feedback_analyzer.analyze_feedback(state, settings_obj))
    graph.add_node("query_processor", lambda state: query_processor.process_query(state, settings_obj))
    graph.add_node("timeout_handler", lambda state: timeout_handler.handle_timeout(state, settings_obj))
    # Split long line to avoid E501 error
    graph.add_node(
        "network_error_handler",
        lambda state: network_error_handler.handle_network_error(state, settings_obj)
    )
    graph.add_node("command_generator", lambda state: command_generator.generate_command(state, settings_obj))
    graph.add_node("command_modifier", lambda state: command_modifier.modify_command(state, settings_obj))
    graph.add_node("result_formatter", lambda state: result_formatter.format_result(state, settings_obj))

    # Define conditional routing based on feedback analysis
    def route_by_feedback(state: GraphState) -> str:
        """Route to appropriate node based on feedback analysis."""
        if not state.is_retry:
            return "query_processor"  # First execution
        elif state.error_type == "TIMEOUT":
            return "timeout_handler"
        elif state.error_type == "NETWORK_ERROR":
            return "network_error_handler"
        else:
            return "query_processor"  # Default path

    # Add edges with conditional routing
    graph.add_edge(START, "feedback_analyzer")
    graph.add_conditional_edges(
        "feedback_analyzer",
        route_by_feedback,
        {
            "query_processor": "query_processor",
            "timeout_handler": "timeout_handler",
            "network_error_handler": "network_error_handler"
        }
    )

    # Add edges for normal flow
    graph.add_edge("query_processor", "command_generator")

    # Add edges for error handling flows
    graph.add_edge("timeout_handler", "command_generator")
    graph.add_edge("network_error_handler", "command_generator")

    # Add edges for command modification and result formatting
    graph.add_edge("command_generator", "command_modifier")
    graph.add_edge("command_modifier", "result_formatter")
    graph.add_edge("result_formatter", END)

    # Whether to compile or not
    if compile:
        return graph.compile()
    return graph
