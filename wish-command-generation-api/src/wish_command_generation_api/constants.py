"""Constants for the command generation API."""

import pathlib

# ドキュメントファイルのパス
DOCS_DIR = pathlib.Path(__file__).parent / "docs"

# ドキュメントファイルの読み込み
def _read_doc_file(filename):
    """ドキュメントファイルを読み込む"""
    file_path = DOCS_DIR / filename
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

# 対話回避のドキュメント
DIALOG_AVOIDANCE_DOC = _read_doc_file("interactive_avoidance.md")
if not DIALOG_AVOIDANCE_DOC:
    DIALOG_AVOIDANCE_DOC = "ERROR: interactive_avoidance.md file not found"

# 高速な代替コマンドのドキュメント
FAST_ALTERNATIVE_DOC = _read_doc_file("fast_alternative_commands.md")
if not FAST_ALTERNATIVE_DOC:
    FAST_ALTERNATIVE_DOC = "ERROR: fast_alternative_commands.md file not found"

# リストファイルのドキュメント
LIST_FILES_DOC = _read_doc_file("list_files.md")
if not LIST_FILES_DOC:
    LIST_FILES_DOC = "ERROR: list_files.md file not found"

# 分割統治のドキュメント
DIVIDE_AND_CONQUER_DOC = _read_doc_file("divide_and_conquer.md")
if not DIVIDE_AND_CONQUER_DOC:
    DIVIDE_AND_CONQUER_DOC = "ERROR: divide_and_conquer.md file not found"
