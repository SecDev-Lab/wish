"""Tests for graph.py."""



from wish_log_analysis.graph import create_log_analysis_graph


def test_create_log_analysis_graph():
    """Test that create_log_analysis_graph creates a graph with the correct structure."""
    # Create a graph
    graph = create_log_analysis_graph(compile=False)

    # Check that the graph has the correct nodes
    assert "log_summarization" in graph.nodes
    assert "command_state_classifier" in graph.nodes
    assert "result_combiner" in graph.nodes


def test_create_log_analysis_graph_compiled():
    """Test that create_log_analysis_graph creates a compiled graph."""
    # Create a compiled graph
    graph = create_log_analysis_graph(compile=True)

    # Check that the graph is compiled
    assert hasattr(graph, "invoke")
