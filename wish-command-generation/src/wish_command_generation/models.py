"""Models for the command generation graph."""

from pydantic import BaseModel, Field
from typing import List, Optional

from wish_models.command_result import CommandInput
from wish_models.wish.wish import Wish


class GraphState(BaseModel):
    """LangGraphの状態を表すクラス。
    
    このクラスはLangGraphの実行中に状態を保持し、各ノード間でデータを受け渡すために使用されます。
    wish-command-generationは、Wishオブジェクトを受け取り、それを実現するための
    複数のコマンド（CommandInput）を出力する役割を持ちます。
    """
    
    wish: Wish
    """処理対象のWishオブジェクト。Wish.wishフィールドには自然言語のコマンド要求が含まれています。"""
    
    context: Optional[List[str]] = None
    """RAGから取得した参考ドキュメントのリスト。コマンド生成の精度向上のために使用します。"""
    
    query: Optional[str] = None
    """RAG検索用のクエリ。RAGシステムで関連ドキュメントを検索するために使用します。"""
    
    command_inputs: List[CommandInput] = Field(default_factory=list)
    """生成されたコマンド入力のリスト。これがグラフの最終的な出力となります。"""
