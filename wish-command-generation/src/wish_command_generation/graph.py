"""Main graph definition for the command generation system."""

from langgraph.graph import StateGraph, END, START

from wish_models.command_result import CommandInput
from wish_models.wish.wish import Wish

from .models import GraphState
from .nodes import command_generation, rag


def create_command_generation_graph(compile=True):
    """コマンド生成グラフを作成する
    
    Args:
        compile: Trueの場合、コンパイル済みのグラフを返す。Falseの場合、コンパイル前のグラフを返す。
    
    Returns:
        コンパイル済みまたはコンパイル前のグラフオブジェクト
    """
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
    
    # コンパイルするかどうか
    if compile:
        return graph.compile()
    return graph
