"""Models for the command generation graph."""

from typing import Any, Dict, List

from pydantic import BaseModel, Field
from wish_models.command_result import CommandInput, CommandResult


class GeneratedCommand(BaseModel):
    """Class representing a generated shell command."""

    command_input: CommandInput
    """コマンド入力情報（コマンドとタイムアウト値）"""

    explanation: str = Field(description="Explanation of what the command does")
    """Explanation of what the command does and why it was chosen."""

    @property
    def command(self) -> str:
        """コマンド文字列を取得"""
        return self.command_input.command

    @property
    def timeout_sec(self) -> int | None:
        """タイムアウト値を取得"""
        return self.command_input.timeout_sec

    @classmethod
    def from_command_input(cls, command_input: CommandInput, explanation: str) -> "GeneratedCommand":
        """CommandInputからGeneratedCommandを作成する"""
        return cls(
            command_input=command_input,
            explanation=explanation
        )


class GraphState(BaseModel):
    """Class representing the state of LangGraph.

    This class is used to maintain state during LangGraph execution and pass data between nodes.
    wish-command-generation-api takes a query and context and outputs generated commands.
    """

    # Input fields - treated as read-only
    query: str = Field(description="User query for command generation")
    """The user's natural language query for command generation."""

    context: Dict[str, Any] = Field(default_factory=dict, description="Context for command generation")
    """Context information for command generation, such as current directory, history, etc."""

    run_id: str | None = None
    """実行ID（StepTraceに使用）"""

    # Intermediate result fields - no Annotated for serial execution
    processed_query: str | None = None
    """Processed and normalized user query."""

    command_candidates: List[CommandInput] | None = None
    """コマンド候補のリスト。各ノードで処理され、最終的に generated_commands の元になる。"""

    # Final output field
    generated_commands: List[GeneratedCommand] | None = None
    """最終的に選択されたコマンド候補に説明を追加したもの。これがAPIの出力となる。"""

    # Error flag
    api_error: bool = False
    """Flag indicating whether an API error occurred during processing."""

    # Feedback fields
    act_result: List[CommandResult] | None = None
    """フィードバック情報（コマンド実行結果）"""

    is_retry: bool = False
    """リトライフラグ（初回実行かリトライか）"""

    error_type: str | None = None
    """エラータイプ（TIMEOUT, NETWORK_ERROR, etc.）"""


class GenerateRequest(BaseModel):
    """Request model for the generate endpoint."""

    query: str = Field(description="User query for command generation")
    """The user's natural language query for command generation."""

    context: Dict[str, Any] = Field(default_factory=dict, description="Context for command generation")
    """Context information for command generation, such as current directory, history, etc."""

    act_result: List[CommandResult] | None = None
    """フィードバック情報（コマンド実行結果）"""

    run_id: str | None = None
    """実行ID（StepTraceに使用）"""


class GenerateResponse(BaseModel):
    """Response model for the generate endpoint."""

    generated_commands: List[GeneratedCommand]
    """The generated commands with explanations."""

    error: str | None = None
    """Error message if an error occurred during processing."""
