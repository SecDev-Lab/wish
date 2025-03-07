"""Log summarization node functions for the log analysis graph."""

import json
import os

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from ..models import GraphState
from ..settings import settings

# Define the prompt template
LOG_SUMMARIZATION_PROMPT = """
あなたは、シェルコマンドとその実行結果のexit_code、stdout、stderrを受け取り、その結果を要約する役割を担っています。
要約結果はコンテキストウィンドウが大きくないLLMに渡されるので、可能な限り短い必要があります。

以下の手順に従ってタスクを完了してください。

1. exit_codeを確認します。exit_codeが0の場合と0以外の場合で要約の方法が異なります。

2. exit_codeが0の場合、次にペネトレーションテストを進めるために何をすべきかわかるための情報をすべて残しつつ、可能な限り短く要約します。特に重要で必ず残すべき情報を例に挙げます:
  - IPアドレス
  - ポート番号
  - ファイルパス
  - ユーザー名
  - バージョン情報
  - 脆弱性・設定ミス項目

3. exit_codeが0以外の場合、コマンドが失敗した理由を簡潔化して要約します。

4. 出力には要約だけを記述してください。

# コマンド
{command}

# exit_code
{exit_code}

# stdout
{stdout}

# stderr
{stderr}
"""


def summarize_log(state: GraphState) -> GraphState:
    """Summarize the log from a command result.

    Args:
        state: The current graph state.

    Returns:
        Updated graph state with log summary.
    """
    # Get the command and exit code from the state
    command = state.command_result.command
    exit_code = state.command_result.exit_code

    # Read stdout and stderr from log_files
    stdout = ""
    stderr = ""
    if state.command_result.log_files:
        if state.command_result.log_files.stdout and os.path.exists(state.command_result.log_files.stdout):
            with open(state.command_result.log_files.stdout, "r", encoding="utf-8") as f:
                stdout = f.read()
        if state.command_result.log_files.stderr and os.path.exists(state.command_result.log_files.stderr):
            with open(state.command_result.log_files.stderr, "r", encoding="utf-8") as f:
                stderr = f.read()

    # Create the prompt
    prompt = PromptTemplate.from_template(LOG_SUMMARIZATION_PROMPT)

    # Initialize the OpenAI model
    model = ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key
    )

    # Create the chain
    chain = prompt | model | StrOutputParser()

    # Generate the summary
    try:
        summary = chain.invoke({
            "command": command,
            "exit_code": exit_code,
            "stdout": stdout,
            "stderr": stderr
        })
    except Exception as e:
        # In case of any error, provide a fallback summary
        summary = f"Error generating summary: {str(e)}"

    # Update the state
    state_dict = state.model_dump()
    state_dict["log_summary"] = summary

    return GraphState(**state_dict)
