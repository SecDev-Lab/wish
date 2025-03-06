"""Main graph definition for the command generation system."""

from langgraph.graph import StateGraph, END, START

from wish_models.command_result import CommandInput
from wish_models.wish.wish import Wish

from .models import GraphState
from .nodes import command_generation, rag


def create_command_generation_graph():
    """コマンド生成グラフを作成する"""
    # グラフの作成
    graph = StateGraph(GraphState)
    
    # ノードの追加
    graph.add_node("query_generation", rag.generate_query)
    graph.add_node("retrieve_documents", rag.retrieve_documents)
    graph.add_node("generate_commands", command_generation.generate_commands)
    
    # エッジの追加（一直線のグラフ）
    graph.add_edge(START, "query_generation")
    graph.add_edge("query_generation", "retrieve_documents")
    graph.add_edge("retrieve_documents", "generate_commands")
    graph.add_edge("generate_commands", END)
    
    # グラフのコンパイル
    return graph.compile()
