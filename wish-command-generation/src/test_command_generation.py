"""Test script for the command generation system."""

from wish_command_generation import create_command_generation_graph
from wish_command_generation.models import GraphState
from wish_models.wish.wish import Wish


def main():
    """メイン関数"""
    # グラフの作成
    graph = create_command_generation_graph()

    # 入力の準備
    wish = Wish.create(wish="Conduct a full port scan on IP 10.10.10.123.")

    # グラフの実行
    initial_state = GraphState(wish=wish)
    result = graph.invoke(initial_state)

    # 結果の表示
    print("Generated commands:")
    for i, cmd in enumerate(result["command_inputs"], 1):
        print(f"{i}. Command: {cmd.command}")
        print(f"   Timeout: {cmd.timeout_sec} seconds")
        print()


if __name__ == "__main__":
    main()
