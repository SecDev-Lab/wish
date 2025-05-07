"""Utility functions for the command generation API."""

def strip_markdown_code_block(text: str) -> str:
    """
    マークダウン形式のコードブロック表記を削除する

    Args:
        text: 処理対象のテキスト

    Returns:
        コードブロック表記が削除されたテキスト
    """
    if not text.startswith("```"):
        return text

    # Extract the content from the code block
    lines = text.split("\n")
    # Remove the first line (```json or similar)
    lines = lines[1:]
    # Remove the last line if it's a closing ```
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    # Join the remaining lines
    return "\n".join(lines).strip()
