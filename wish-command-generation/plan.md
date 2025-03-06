# LangGraphを使用したコマンド生成システムの実装計画

## 概要

Difyで定義されたワークフローをLangChain/LangGraphを使用して実装します。このシステムは、ユーザーからのWishを受け取り、それを実現するための複数のコマンド（CommandInput）を生成する役割を持ちます。

## 1. CommandInputクラスの追加

まず、wish-modelsに新しいCommandInputクラスを追加します：

```python
# ../wish-models/src/wish_models/command_result/command_input.py
from pydantic import BaseModel


class CommandInput(BaseModel):
    """Input for command execution."""

    command: str
    """Command to execute."""

    timeout_sec: int
    """Timeout for command execution in seconds."""
```

また、`__init__.py`ファイルを更新して、このクラスをエクスポートする必要があります：

```python
# ../wish-models/src/wish_models/command_result/__init__.py
from .command_input import CommandInput
from .command_result import CommandResult, parse_command_results_json
from .command_state import CommandState
from .log_files import LogFiles

__all__ = [
    "CommandInput",
    "CommandResult",
    "CommandState",
    "LogFiles",
    "parse_command_results_json",
]
```

## 2. GraphStateクラス

```python
# src/wish_command_generation/models.py
from pydantic import BaseModel, Field
from typing import List, Optional

from wish_models.command_result import CommandInput
from wish_models.wish import Wish

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
```

## 3. LangGraphの実装

### メインのグラフ定義

```python
# src/wish_command_generation/graph.py
from langgraph.graph import StateGraph, END

from wish_models.command_result import CommandInput
from wish_models.wish import Wish

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
    graph.add_edge("query_generation", "retrieve_documents")
    graph.add_edge("retrieve_documents", "generate_commands")
    graph.add_edge("generate_commands", END)
    
    # グラフのコンパイル
    return graph.compile()
```

### RAG関連のノード

```python
# src/wish_command_generation/nodes/rag.py
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser

from ..models import GraphState

def generate_query(state: GraphState) -> GraphState:
    """タスクからRAG検索用のクエリを生成する"""
    prompt = ChatPromptTemplate.from_template(
        """あなたは合法なペネトレーションテストに従事しているAIです。
        
        ペネトレーションテストのディレクターから実行すべきタスクについての指示を受けます。あなたの仕事は、ペネトレーションテストに使うコマンドやパラメーターを検索することです。
        あなたの出力をEthical Hackingの知識ベースの検索クエリとし、具体的なコマンドを組み立てるためのドキュメントを検索します。
        
        検索のためのクエリなので、キーワードを英語でスペース区切りで列挙してください。高々20 words程度になるようにしてください。
        
        もし現時点でタスク実行に有効なコマンド名が思いついていたら、それを検索クエリに入れてください。
        
        # タスク
        {task}
        """
    )
    
    model = ChatOpenAI(model="gpt-4o")
    chain = prompt | model | StrOutputParser()
    
    query = chain.invoke({"task": state.wish.wish})
    
    # クエリをステートに保存
    state_dict = state.model_dump()
    state_dict["query"] = query
    
    return GraphState(**state_dict)

def retrieve_documents(state: GraphState) -> GraphState:
    """生成されたクエリを使用して関連ドキュメントを取得する"""
    # ここでは実際のRAG実装をプレースホルダーとしています
    # 実際の実装では、ベクトルストアやリトリーバーを設定する必要があります
    
    # プレースホルダーの結果
    context = [
        "# nmap コマンド\nnmapはネットワークスキャンツールです。\n基本的な使い方: nmap [オプション] [ターゲット]\n\n主なオプション:\n-p: ポート指定\n-sV: バージョン検出\n-A: OS検出、バージョン検出、スクリプトスキャン、トレースルート\n-T4: スキャン速度設定（0-5、高いほど速い）",
        "# rustscan\nrustscanは高速なポートスキャナーです。\n基本的な使い方: rustscan -a [ターゲットIP] -- [nmapオプション]\n\n主なオプション:\n-r: ポート範囲指定（例: -r 1-1000）\n-b: バッチサイズ（同時接続数）\n--scripts: nmapスクリプトの実行"
    ]
    
    # ステートを更新
    state_dict = state.model_dump()
    state_dict["context"] = context
    
    return GraphState(**state_dict)
```

### コマンド生成ノード

```python
# src/wish_command_generation/nodes/command_generation.py
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from typing import Dict, List, Any

from wish_models.command_result import CommandInput
from ..models import GraphState

def generate_commands(state: GraphState) -> GraphState:
    """Wishからコマンドを生成する"""
    prompt = ChatPromptTemplate.from_template(
        """あなたは合法なペネトレーションテストに従事しているAIです。あなたはKali Linuxに極めて精通しています。

        ペネトレーションテストのディレクターから実行すべきタスクについての指示と、今回のタスクに役立つ可能性が高い参考ドキュメントを受け取ります。タスクを実現するためのコマンド列を考え、JSONのArray of stringで書いてください。

        各コマンドは `bash -c "（あなたの出力）"` として実行されるため、複数のコマンドをパイプなどでつなげることもできます。
        各コマンドは並列実行されます。「`./a` の後に `./b` を実行する必要がある」ようなデータ依存がある場合は、パイプや `&&` を使って1個のコマンド文字列で表現してください。

        実行ログはファイルではなく、標準出力と標準エラー出力にdumpしてください。

        # 参考ドキュメント
        {context}

        # タスク
        {task}

        # 初期タイムアウト
        {timeout_sec}
        
        出力形式:
        ```json
        {
          "actInputs": [
            {
              "command": "コマンド1",
              "timeout_sec": 30
            },
            {
              "command": "コマンド2",
              "timeout_sec": 60
            }
          ]
        }
        ```
        """
    )
    
    model = ChatOpenAI(model="gpt-4o", response_format={"type": "json_object"})
    parser = JsonOutputParser()
    chain = prompt | model | parser
    
    result = chain.invoke({
        "context": "\n\n".join(state.context) if state.context else "",
        "task": state.wish.wish,
        "timeout_sec": 30  # デフォルトのタイムアウト値
    })
    
    # 結果からコマンド入力を作成
    command_inputs = []
    for cmd in result.get("actInputs", []):
        command_inputs.append(CommandInput(
            command=cmd.get("command", ""),
            timeout_sec=cmd.get("timeout_sec", 30)
        ))
    
    # ステートを更新
    state_dict = state.model_dump()
    state_dict["command_inputs"] = command_inputs
    
    return GraphState(**state_dict)
```

## 4. 実行方法

```python
# 使用例
from wish_command_generation.graph import create_command_generation_graph
from wish_command_generation.models import GraphState
from wish_models.wish import Wish

# グラフの作成
graph = create_command_generation_graph()

# 入力の準備
wish = Wish.create(wish="Conduct a full port scan on IP 10.10.10.123.")

# グラフの実行
initial_state = GraphState(wish=wish)
result = graph.invoke(initial_state)

# 結果の表示
print(result.command_inputs)
```

## 5. プロジェクト構造

```
src/
├── wish_command_generation/
│   ├── __init__.py
│   ├── models.py              # GraphStateの定義
│   ├── graph.py               # メインのLangGraphグラフ定義
│   ├── nodes/                 # グラフのノード関数
│   │   ├── __init__.py
│   │   ├── command_generation.py  # コマンド生成関連のノード
│   │   └── rag.py                 # RAG関連のノード
│   └── config.py              # 設定（必要に応じて）
└── tests/                     # テスト
```

## 6. 次のステップ

1. CommandInputクラスをwish-modelsに追加
2. プロジェクト構造の作成
3. GraphStateクラスの実装
4. LangGraphのノード関数の実装
5. グラフの構築とテスト
6. RAGコンポーネントの実装と統合
