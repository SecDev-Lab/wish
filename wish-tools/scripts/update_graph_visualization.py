#!/usr/bin/env python
"""
Graph visualization script for RapidPen Tools

Load the LangGraph graph definitions and save them as SVG visualizations.
"""

import importlib
import sys
from pathlib import Path
from typing import Dict

import graphviz
from langgraph.graph import END, StateGraph

# Get the project root directory
ROOT_DIR = Path(__file__).parent.parent.absolute()
SRC_DIR = ROOT_DIR / "src"
MODELS_DIR = Path(ROOT_DIR).parent / "rapidpen-models" / "src"
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(SRC_DIR))
sys.path.insert(0, str(MODELS_DIR))

# SVG file output destination
SVG_DIR = ROOT_DIR / "docs" / "images"
SVG_DIR.mkdir(exist_ok=True, parents=True)

# README file path
README_PATH = ROOT_DIR / "README.md"


def extract_graph_config(graph: StateGraph) -> Dict:
    """
    StateGraphオブジェクトからグラフ設定を抽出する

    Args:
        graph: StateGraphオブジェクト

    Returns:
        グラフ設定の辞書
    """
    # ノードの抽出
    nodes = list(graph.nodes)

    # エントリーポイントの抽出
    entry_point = None
    if hasattr(graph, "entry_point"):
        entry_point = graph.entry_point

    # 終了ポイントの抽出
    finish_points = []
    if hasattr(graph, "finish_points"):
        finish_points = list(graph.finish_points)

    # エッジの抽出
    edges = []
    conditional_edges = {}

    # グラフ構造からエッジを抽出
    if hasattr(graph, "edges"):
        # 新しいバージョンではgraph.edgesにエッジ情報がある
        # edgesがセットの場合（タプルのセット）
        if isinstance(graph.edges, set):
            for edge in graph.edges:
                if isinstance(edge, tuple) and len(edge) >= 2:
                    source, target = edge[0], edge[1]
                    if target == END:
                        # ENDノードは終了ポイントとして扱う
                        if source not in finish_points:
                            finish_points.append(source)
                    else:
                        edges.append((source, target))
        # edgesが辞書の場合
        elif hasattr(graph.edges, "items"):
            for source, targets in graph.edges.items():
                for target in targets:
                    if target == END:
                        # ENDノードは終了ポイントとして扱う
                        if source not in finish_points:
                            finish_points.append(source)
                    else:
                        edges.append((source, target))
    elif hasattr(graph, "_graph"):
        # 古いバージョンではgraph._graphにエッジ情報がある
        for source, targets in graph._graph.items():
            for target in targets:
                if target == END:
                    # ENDノードは終了ポイントとして扱う
                    if source not in finish_points:
                        finish_points.append(source)
                else:
                    edges.append((source, target))

    # 条件分岐エッジの抽出
    if hasattr(graph, "branches"):
        # 新しいバージョンではgraph.branchesに条件分岐情報がある
        if hasattr(graph.branches, "items"):
            for source, branch_info in graph.branches.items():
                if hasattr(branch_info, "items"):
                    for _condition_func, branch in branch_info.items():
                        if hasattr(branch, "ends") and branch.ends:
                            for condition, target in branch.ends.items():
                                if target == "__end__" or target == END:
                                    # ENDノードは終了ポイントとして扱う
                                    if source not in finish_points:
                                        finish_points.append(source)
                                else:
                                    # 条件分岐エッジを通常のエッジとして追加
                                    edges.append((source, target))
                                    # 条件情報を保存
                                    if source not in conditional_edges:
                                        conditional_edges[source] = {}
                                    conditional_edges[source][target] = condition
    # 古いバージョンの条件分岐エッジの抽出
    elif hasattr(graph, "_conditional_edges") and hasattr(graph, "_conditional_edge_branches"):
        for source, _condition_func in graph._conditional_edges.items():
            for condition, target in graph._conditional_edge_branches[source].items():
                if target == END:
                    # ENDノードは終了ポイントとして扱う
                    if source not in finish_points:
                        finish_points.append(source)
                else:
                    # 条件分岐エッジを通常のエッジとして追加
                    edges.append((source, target))
                    # 条件情報を保存
                    if source not in conditional_edges:
                        conditional_edges[source] = {}
                    conditional_edges[source][target] = condition

    return {
        "nodes": nodes,
        "entry_point": entry_point,
        "finish_points": finish_points,
        "edges": edges,
        "conditional_edges": conditional_edges
    }


def generate_graph_visualization():
    """Visualize the graphs and save them as SVG"""
    # モジュールとグラフ設定のマッピング
    module_configs = {
        "tool_step_trace": {
            "module_path": "rapidpen_tools.tool_step_trace",
            "filename": "tool_step_trace_graph.svg",
            "title": "Tool Step Trace Graph"
        }
    }

    # 各モジュールからグラフを生成
    for name, config in module_configs.items():
        try:
            # モジュールをインポート
            module = importlib.import_module(config["module_path"])

            # build_graph関数を呼び出してグラフを取得
            if hasattr(module, "build_graph"):
                graph = module.build_graph()

                # グラフ設定を抽出
                graph_config = extract_graph_config(graph)

                # グラフ設定にファイル名とタイトルを追加
                graph_config["filename"] = config["filename"]
                graph_config["title"] = config["title"]

                # グラフを可視化
                visualize_graph(name, graph_config)
            else:
                print(f"Warning: Module {config['module_path']} does not have build_graph function")
        except Exception as e:
            print(f"Error processing module {config['module_path']}: {e}")


def visualize_graph(name: str, config: Dict):
    """
    グラフを可視化してSVGファイルに保存する

    Args:
        name: グラフの名前
        config: グラフ設定の辞書
    """
    # Create a graphviz object
    dot = graphviz.Digraph(comment=config["title"])
    dot.attr(rankdir="LR")  # Layout from left to right

    # Add nodes
    for node_name in config["nodes"]:
        if node_name == config["entry_point"]:
            dot.node(node_name, node_name, shape="circle", style="filled", fillcolor="green")
        elif node_name in config["finish_points"]:
            dot.node(node_name, node_name, shape="circle", style="filled", fillcolor="red")
        else:
            dot.node(node_name, node_name, shape="box", style="filled", fillcolor="lightblue")

    # Add edges
    for source, target in config["edges"]:
        # 条件分岐エッジの場合はラベルを追加
        has_conditional = "conditional_edges" in config
        in_source = has_conditional and source in config["conditional_edges"]
        in_target = in_source and target in config["conditional_edges"][source]
        if in_target:
            condition = config["conditional_edges"][source][target]
            dot.edge(source, target, label=condition)
        else:
            dot.edge(source, target)

    # Save as SVG
    svg_path = SVG_DIR / config["filename"]
    dot.render(svg_path.with_suffix(""), format="svg", cleanup=True)
    print(f"Graph visualization saved to {svg_path}")

    # Update README.md
    update_readme(config["title"], config["filename"])


def update_readme(graph_title: str, svg_filename: str):
    """Update the README.md file with graph visualization"""
    # Create relative path to the SVG file
    relative_svg_path = f"docs/images/{svg_filename}"

    # Read the current content of README.md
    if README_PATH.exists():
        content = README_PATH.read_text()
    else:
        content = "# RapidPen Tools\n\n"
        content += "RapidPen Toolsモジュールは、RapidPenの各モジュールで使用される共通ツールを提供するモジュールです。\n"

    # Check if there is a graph visualization section
    graph_section_title = "## ワークフローグラフ"
    graph_image_ref = f"![{graph_title}]({relative_svg_path})"

    if graph_section_title in content:
        # If the section exists, check if this specific graph is already included
        if graph_image_ref in content:
            print(f"Graph {graph_title} already exists in README.md")
        else:
            # Add this graph to the existing section
            import re
            section_pattern = re.compile(f"{graph_section_title}.*?(?=^#|$)", re.DOTALL | re.MULTILINE)
            section_match = section_pattern.search(content)

            if section_match:
                section_content = section_match.group(0)
                updated_section = f"{section_content}\n\n{graph_image_ref}\n"
                content = content.replace(section_content, updated_section)
                README_PATH.write_text(content)
                print(f"Added {graph_title} to existing graph section in README.md")
            else:
                # This shouldn't happen if the section title was found
                print("Error: Could not locate the graph section content")
    else:
        # Add a new graph visualization section
        content += f"\n\n{graph_section_title}\n\n{graph_image_ref}\n"
        README_PATH.write_text(content)
        print(f"Added new graph section with {graph_title} to README.md")


if __name__ == "__main__":
    generate_graph_visualization()
