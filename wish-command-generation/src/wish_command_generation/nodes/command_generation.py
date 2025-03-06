"""Command generation node functions for the command generation graph."""

from typing import Dict, List, Any

from wish_models.command_result import CommandInput
from ..models import GraphState


def generate_commands(state: GraphState) -> GraphState:
    """Wishからコマンドを生成する"""
    # テスト用のモック実装
    # 実際の実装では、LangChainを使用してコマンドを生成します
    
    # タスクに基づいて簡単なコマンドを生成
    task = state.wish.wish.lower()
    command_inputs = []
    
    if "port scan" in task:
        # ポートスキャンのコマンドを生成
        if "10.10.10.123" in task:
            command_inputs = [
                CommandInput(command="nmap -p 1-1000 10.10.10.123", timeout_sec=30),
                CommandInput(command="rustscan -a 10.10.10.123 -- -sV", timeout_sec=60)
            ]
        else:
            # IPアドレスが指定されていない場合は、一般的なコマンドを生成
            command_inputs = [
                CommandInput(command="nmap -p 1-1000 [TARGET_IP]", timeout_sec=30),
                CommandInput(command="rustscan -a [TARGET_IP] -- -sV", timeout_sec=60)
            ]
    elif "vulnerability" in task:
        # 脆弱性スキャンのコマンドを生成
        command_inputs = [
            CommandInput(command="nikto -h [TARGET_IP]", timeout_sec=120),
            CommandInput(command="nmap -sV --script vuln [TARGET_IP]", timeout_sec=180)
        ]
    else:
        # デフォルトのコマンドを生成
        command_inputs = [
            CommandInput(command="nmap -sC -sV [TARGET_IP]", timeout_sec=60),
            CommandInput(command="dirb http://[TARGET_IP]/ /usr/share/dirb/wordlists/common.txt", timeout_sec=120)
        ]
    
    # ステートを更新
    state_dict = state.model_dump()
    state_dict["command_inputs"] = command_inputs
    
    return GraphState(**state_dict)
