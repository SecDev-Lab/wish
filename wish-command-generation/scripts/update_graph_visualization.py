#!/usr/bin/env python
"""
グラフ可視化スクリプト

LangGraphのグラフ定義を読み込み、SVG形式で可視化して保存します。
"""

import os
import sys
from pathlib import Path
import graphviz
import importlib.util

# プロジェクトのルートディレクトリを取得
ROOT_DIR = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(ROOT_DIR))

# docs/designディレクトリが存在しない場合は作成
DOCS_DIR = ROOT_DIR / "docs"
DOCS_DIR.mkdir(exist_ok=True)

# SVGファイルの出力先
SVG_PATH = DOCS_DIR / "graph.svg"
MD_PATH = DOCS_DIR / "design.md"


def generate_graph_visualization():
    """グラフを可視化してSVGとして保存する"""
    # グラフモジュールをインポート
    from wish_command_generation.graph import create_command_generation_graph
    
    # グラフを作成（コンパイル前のグラフオブジェクトを取得）
    graph = create_command_generation_graph(compile=False)
    
    # graphvizオブジェクトを作成
    dot = graphviz.Digraph(comment="Command Generation Graph")
    dot.attr(rankdir="LR")  # 左から右へのレイアウト
    
    # ノードを追加
    for node_name in graph.nodes:
        if node_name == "START":
            dot.node(node_name, node_name, shape="circle", style="filled", fillcolor="green")
        elif node_name == "END":
            dot.node(node_name, node_name, shape="circle", style="filled", fillcolor="red")
        else:
            dot.node(node_name, node_name, shape="box", style="filled", fillcolor="lightblue")
    
    # エッジの形式を確認
    print("Edges format:", graph.edges)
    print("Edges type:", type(graph.edges))
    
    # エッジを追加
    for edge in graph.edges:
        if isinstance(edge, tuple) and len(edge) >= 2:
            source, target = edge[0], edge[1]
            # 条件付きエッジの場合はラベルを追加（3番目の要素がある場合）
            if len(edge) > 2 and edge[2]:
                dot.edge(str(source), str(target), label=str(edge[2]))
            else:
                dot.edge(str(source), str(target))
        elif isinstance(edge, dict) and "source" in edge and "target" in edge:
            source = edge["source"]
            target = edge["target"]
            # 条件付きエッジの場合はラベルを追加
            if "condition" in edge:
                dot.edge(source, target, label=edge["condition"])
            else:
                dot.edge(source, target)
        else:
            print(f"Skipping edge with unknown format: {edge}")
    
    # SVGとして保存
    dot.render(SVG_PATH.with_suffix(""), format="svg", cleanup=True)
    print(f"Graph visualization saved to {SVG_PATH}")
    
    # design.mdを更新
    update_design_md()


def update_design_md():
    """design.mdファイルを更新する"""
    # ファイルが存在しない場合は作成
    if not MD_PATH.exists():
        MD_PATH.write_text("""# Command Generation Design

This document describes the design of the command generation system.

## Graph Visualization

![Command Generation Graph](graph.svg)

""")
        print(f"Created {MD_PATH}")
        return
    
    # ファイルが存在する場合は内容を読み込む
    content = MD_PATH.read_text()
    
    # グラフ可視化セクションがあるか確認
    if "## Graph Visualization" in content and "![Command Generation Graph](graph.svg)" in content:
        # 既に正しい参照がある場合は何もしない
        print(f"No changes needed in {MD_PATH}")
    else:
        # グラフ可視化セクションがない場合は追加
        if "## Graph Visualization" not in content:
            content += "\n\n## Graph Visualization\n\n![Command Generation Graph](graph.svg)\n"
        else:
            # セクションはあるが画像参照がない場合
            import re
            content = re.sub(
                r"## Graph Visualization\s*\n",
                "## Graph Visualization\n\n![Command Generation Graph](graph.svg)\n",
                content
            )
        
        # 更新した内容を書き込む
        MD_PATH.write_text(content)
        print(f"Updated {MD_PATH}")


if __name__ == "__main__":
    generate_graph_visualization()
