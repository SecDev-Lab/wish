# Wish Tools Framework

Wish Toolsは、wish フレームワーク用の拡張可能なツール抽象化フレームワークです。ペネトレーションテストツールを統一的なインターフェースで使用できるようにし、LLM による自動的なツール選択とコマンド生成を可能にします。

## 特徴

- **統一インターフェース**: 異なるツールを共通のAPIで操作
- **自動ツール発見**: 新しいツールの自動登録
- **LLM統合**: ツールの機能をLLMが理解できる形で提供
- **テスト機能**: 各ツールの動作確認とテスト
- **ドキュメント生成**: ツールの使用方法を自動生成
- **フォールバック機能**: 専用ツールがない場合のbashフォールバック

## インストールと使用方法

### 基本的な使用方法

```python
from wish_tools.framework.registry import tool_registry
from wish_tools.framework.base import ToolContext, CommandInput

# 利用可能なツールを一覧表示
tools = tool_registry.list_tools()
for tool in tools:
    print(f"{tool.name}: {tool.description}")

# ツールを取得して実行
tool = tool_registry.get_tool('bash')
context = ToolContext(
    working_directory='/tmp',
    run_id='example'
)

# コマンドを生成
command = tool.generate_command(
    capability='execute',
    parameters={
        'command': 'nmap -sS -p 22,80,443 192.168.1.0/24',
        'category': 'network'
    }
)

# コマンドを実行
result = await tool.execute(command, context)
print(f"Success: {result.success}")
print(f"Output: {result.output}")
```

### ツール機能の検索

```python
# カテゴリ別にツールを検索
exploit_tools = tool_registry.list_by_category('exploitation')
fallback_tools = tool_registry.list_by_category('fallback')

# タグで検索
pentesting_tools = tool_registry.list_by_tag('pentesting')

# キーワード検索
search_results = tool_registry.search_tools('metasploit')
```

## 利用可能なツール

### 専用ツール

#### msfconsole (Exploitation)
- **exploit**: エクスプロイト実行
- **auxiliary**: 補助モジュール実行
- **search**: モジュール検索
- **info**: モジュール情報取得

### フォールバックツール

#### bash (Universal Fallback)
- **execute**: 任意のシェルコマンド実行
- **script**: カスタムスクリプト実行
- **tool_combination**: 複数ツールの組み合わせ

専用ツールが利用できない場合の最後の手段として使用されます。

## ツールの追加

新しいツールを追加するには、`BaseTool` を継承したクラスを作成します：

```python
from wish_tools.framework.base import BaseTool, ToolMetadata, ToolCapability

class MyTool(BaseTool):
    def _build_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="mytool",
            version="1.0.0", 
            description="My custom tool",
            author="Me",
            category="custom",
            capabilities=[
                ToolCapability(
                    name="scan",
                    description="Perform custom scanning",
                    parameters={
                        "target": "Target to scan",
                        "options": "Scan options"
                    },
                    examples=["mytool -t 192.168.1.1 -v"]
                )
            ],
            requirements=["mytool"],
            tags=["custom", "scanning"]
        )
    
    async def validate_availability(self):
        # ツールの利用可能性をチェック
        return True, None
    
    async def execute(self, command, context):
        # ツールを実行
        pass
    
    def generate_command(self, capability, parameters, context=None):
        # LLM用のコマンド生成
        pass
```

ツールは自動的に発見・登録されます。

## テストとドキュメント生成

### ツールのテスト実行

```bash
# 特定のツールをテスト
uv run python scripts/test_tools.py --tool bash

# 全ツールをテスト  
uv run python scripts/test_tools.py

# テストレポートを保存
uv run python scripts/test_tools.py --save-reports
```

### ドキュメント生成

```bash
# ツールドキュメントを生成
uv run python scripts/generate_tool_docs.py

# 特定の種類のドキュメントのみ生成
uv run python scripts/generate_tool_docs.py --index --matrix
```

## LLM統合

このフレームワークは、LLMが適切なツールと機能を選択できるよう設計されています。

### ツール選択の優先順位

1. **専用ツール優先**: 可能な限り専用ツールを使用
2. **bashフォールバック**: 専用ツールがない場合のみbashを使用

### LLM向けメタデータ

各ツールは以下の情報をLLMに提供します：

- **機能(Capabilities)**: ツールができること
- **パラメータ**: 各機能で必要な入力
- **例**: 具体的な使用例
- **要件**: システム要件

## アーキテクチャ

```
wish-tools/
├── framework/          # コアフレームワーク
│   ├── base.py        # ツールインターフェース
│   ├── registry.py    # ツール登録・管理
│   └── testing.py     # テストフレームワーク
├── tools/             # ツール実装
│   ├── bash.py        # Bashツール（フォールバック）
│   └── msfconsole.py  # Metasploitツール
└── scripts/           # 開発支援スクリプト
    ├── test_tools.py
    └── generate_tool_docs.py
```

## レガシーツール（後方互換性）

以下のレガシーツールは後方互換性のため残されています：

### Tool Step Trace

```python
from wish_tools.tool_step_trace import main as step_trace_main

result = step_trace_main(
    run_id="実行ID",
    trace_name="トレース名", 
    trace_message="トレースメッセージ"
)
```

### Base64 Encoder

```python  
from wish_tools.to_base64 import main as to_base64

encoded = to_base64("Hello, World!")
```

これらは将来的に新しいフレームワークインターフェースに移行予定です。

## 開発とコントリビューション

### 開発環境セットアップ

```bash
# 開発環境のセットアップ
make dev-setup

# または手動で：
uv sync                       # 依存関係のインストール
uv run pre-commit install    # pre-commitフックのインストール
```

### 開発ワークフロー

```bash
# 新しいツールの追加
make add-tool TOOL_NAME=mytool

# ドキュメント生成
make docs

# テスト実行
make test

# 開発チェック（リント + テスト + ドキュメント確認）
make dev-check

# リリース前チェック
make release-check
```

### 自動化された品質管理

#### **Pre-commit Hooks**
ツールファイルを変更時に自動実行：
- ドキュメント生成
- テスト実行

#### **GitHub Actions**
プルリクエスト時に自動チェック：
- ドキュメントが最新か確認
- すべてのテストをパス
- コード品質チェック

#### **Make タスク**
```bash
make help  # 利用可能なコマンドを表示
```

### コントリビューションガイドライン

1. 新しいツールを追加する場合は `BaseTool` を継承してください
2. 適切なテストケースを作成してください
3. ドキュメントが自動生成されることを確認してください
4. 安全性チェック（`validate_command`）を実装してください
