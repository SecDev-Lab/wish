"""Document splitter for HackTricks markdown files."""

import re
from dataclasses import dataclass
from typing import Any


@dataclass
class DocumentChunk:
    """A chunk of document with metadata."""

    text: str
    metadata: dict[str, Any]
    chunk_id: int
    total_chunks: int


class HackTricksMarkdownSplitter:
    """Custom markdown splitter for HackTricks documents."""

    def __init__(self, chunk_size: int = 1500, chunk_overlap: int = 300) -> None:
        """Initialize splitter with chunk settings."""
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = [
            # Headers (hierarchical order)
            "\n# ",
            "\n## ",
            "\n### ",
            "\n#### ",
            # Code blocks boundaries
            "\n```",
            # Table boundaries
            "\n\n|",
            # Paragraphs
            "\n\n",
            # Lines
            "\n",
            # Words
            " ",
            "",
        ]

    def split_text(self, text: str) -> list[str]:
        """Split text into chunks while preserving structure."""
        # Protect code blocks
        code_blocks = re.findall(r"```[^\n]*\n.*?\n```", text, re.DOTALL)
        for i, block in enumerate(code_blocks):
            text = text.replace(block, f"{{CODE_BLOCK_{i}}}")

        # Protect tables
        table_pattern = r"(\|[^\n]*\n\|[\s-]*\|[^\n]*\n(?:\|[^\n]*\n)*)"
        tables = re.findall(table_pattern, text, re.DOTALL)
        for i, table in enumerate(tables):
            text = text.replace(table, f"{{TABLE_{i}}}")

        # Split by separators
        chunks = self._recursive_split(text, self.separators)

        # Restore code blocks and tables
        for i, block in enumerate(code_blocks):
            chunks = [chunk.replace(f"{{CODE_BLOCK_{i}}}", block) for chunk in chunks]

        for i, table in enumerate(tables):
            chunks = [chunk.replace(f"{{TABLE_{i}}}", table) for chunk in chunks]

        # Apply overlap
        if self.chunk_overlap > 0:
            chunks = self._apply_overlap(chunks)

        return chunks

    def _recursive_split(self, text: str, separators: list[str]) -> list[str]:
        """Recursively split text using separators."""
        if not separators:
            return [text]

        separator = separators[0]
        if not separator:
            # Split by character
            return self._split_by_size(text)

        parts = text.split(separator)
        chunks: list[str] = []
        current_chunk = ""

        for i, part in enumerate(parts):
            # Add separator back (except for first part)
            if i > 0 and separator.strip():
                part = separator.strip() + " " + part

            if len(current_chunk) + len(part) <= self.chunk_size:
                current_chunk += part
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())

                # If part is still too large, split it recursively
                if len(part) > self.chunk_size:
                    sub_chunks = self._recursive_split(part, separators[1:])
                    chunks.extend(sub_chunks)
                else:
                    current_chunk = part

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def _split_by_size(self, text: str) -> list[str]:
        """Split text by size when no separators work."""
        chunks = []
        # Ensure step is an integer
        step = max(1, int(self.chunk_size - self.chunk_overlap))
        for i in range(0, len(text), step):
            chunk = text[i : i + self.chunk_size]
            if chunk:
                chunks.append(chunk)
        return chunks

    def _apply_overlap(self, chunks: list[str]) -> list[str]:
        """Apply overlap between chunks."""
        if len(chunks) <= 1:
            return chunks

        overlapped_chunks = []
        # Maximum allowed chunk size to prevent token limit issues
        # Conservative limit for technical content with code/tables
        max_allowed_size = int(min(self.chunk_size * 1.5, 1500))  # Even more conservative

        for i, chunk in enumerate(chunks):
            if i == 0:
                # Ensure even first chunk respects limit
                if len(chunk) > max_allowed_size:
                    chunk = chunk[:max_allowed_size]
                overlapped_chunks.append(chunk)
            else:
                # Get overlap from previous chunk
                prev_chunk = overlapped_chunks[i - 1]  # Use the already processed chunk
                overlap_text = self._get_overlap_text(prev_chunk)

                # Check if adding overlap doesn't exceed chunk size too much
                combined = overlap_text + chunk
                if len(combined) <= max_allowed_size:
                    overlapped_chunks.append(combined)
                else:
                    # If too large, just use chunk without overlap
                    if len(chunk) > max_allowed_size:
                        chunk = chunk[:max_allowed_size]
                    overlapped_chunks.append(chunk)

        return overlapped_chunks

    def _get_overlap_text(self, text: str) -> str:
        """Get overlap text from the end of a chunk."""
        if len(text) <= self.chunk_overlap:
            return text + "\n\n"

        # Try to find a good split point (sentence or paragraph)
        overlap_start = len(text) - self.chunk_overlap
        overlap_text = text[overlap_start:]

        # Look for sentence boundaries
        sentence_end = max(
            overlap_text.rfind(". "),
            overlap_text.rfind("! "),
            overlap_text.rfind("? "),
        )

        if sentence_end > 0:
            return overlap_text[sentence_end + 2 :] + "\n\n"

        # Look for paragraph boundaries
        para_end = overlap_text.rfind("\n\n")
        if para_end > 0:
            return overlap_text[para_end + 2 :] + "\n\n"

        return overlap_text + "\n\n"
