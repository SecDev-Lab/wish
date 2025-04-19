#!/usr/bin/env python
"""
Graph visualization script

Load the LangGraph graph definition and save it as an SVG visualization.
"""

import sys
from pathlib import Path

import graphviz

# Get the project root directory
ROOT_DIR = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(ROOT_DIR))

# Create the docs/design directory if it doesn't exist
DOCS_DIR = ROOT_DIR / "docs"
DOCS_DIR.mkdir(exist_ok=True)

# SVG file output destination
SVG_PATH = DOCS_DIR / "graph.svg"
MD_PATH = DOCS_DIR / "design.md"


def generate_graph_visualization():
    """Visualize the graph and save it as SVG"""
    # Import the graph module
    from wish_models.settings import Settings

    from wish_log_analysis_api.graph import create_log_analysis_graph

    # Create settings object
    settings_obj = Settings()

    # Create the graph (get the pre-compiled graph object)
    graph = create_log_analysis_graph(settings_obj=settings_obj, compile=False)

    # Create a graphviz object
    dot = graphviz.Digraph(comment="Log Analysis Graph")
    dot.attr(rankdir="LR")  # Layout from left to right

    # Add nodes
    for node_name in graph.nodes:
        if node_name == "START":
            dot.node(node_name, node_name, shape="circle", style="filled", fillcolor="green")
        elif node_name == "END":
            dot.node(node_name, node_name, shape="circle", style="filled", fillcolor="red")
        else:
            dot.node(node_name, node_name, shape="box", style="filled", fillcolor="lightblue")

    # Check the edge format
    print("Edges format:", graph.edges)
    print("Edges type:", type(graph.edges))

    # Add edges
    for edge in graph.edges:
        if isinstance(edge, tuple) and len(edge) >= 2:
            source, target = edge[0], edge[1]
            # Add a label for conditional edges (if there is a third element)
            if len(edge) > 2 and edge[2]:
                dot.edge(str(source), str(target), label=str(edge[2]))
            else:
                dot.edge(str(source), str(target))
        elif isinstance(edge, dict) and "source" in edge and "target" in edge:
            source = edge["source"]
            target = edge["target"]
            # Add a label for conditional edges
            if "condition" in edge:
                dot.edge(source, target, label=edge["condition"])
            else:
                dot.edge(source, target)
        else:
            print(f"Skipping edge with unknown format: {edge}")

    # Save as SVG
    dot.render(SVG_PATH.with_suffix(""), format="svg", cleanup=True)
    print(f"Graph visualization saved to {SVG_PATH}")

    # Update design.md
    update_design_md()


def update_design_md():
    """Update the design.md file"""
    # Create the file if it doesn't exist
    if not MD_PATH.exists():
        MD_PATH.write_text("""# Log Analysis Design

This document describes the design of the log analysis system.

## Graph Visualization

![Log Analysis Graph](graph.svg)

""")
        print(f"Created {MD_PATH}")
        return

    # Load the content if the file exists
    content = MD_PATH.read_text()

    # Check if there is a graph visualization section
    if "## Graph Visualization" in content and "![Log Analysis Graph](graph.svg)" in content:
        # Do nothing if the correct reference already exists
        print(f"No changes needed in {MD_PATH}")
    else:
        # Add a graph visualization section if it doesn't exist
        if "## Graph Visualization" not in content:
            content += "\n\n## Graph Visualization\n\n![Log Analysis Graph](graph.svg)\n"
        else:
            # If the section exists but there is no image reference
            import re
            content = re.sub(
                r"## Graph Visualization\s*\n",
                "## Graph Visualization\n\n![Log Analysis Graph](graph.svg)\n",
                content
            )

        # Write the updated content
        MD_PATH.write_text(content)
        print(f"Updated {MD_PATH}")


if __name__ == "__main__":
    generate_graph_visualization()
