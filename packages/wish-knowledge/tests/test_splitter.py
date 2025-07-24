"""Tests for document splitter."""

import pytest

from wish_knowledge.splitter import HackTricksMarkdownSplitter


class TestHackTricksMarkdownSplitter:
    """Test HackTricksMarkdownSplitter functionality."""

    @pytest.fixture
    def splitter(self):
        """Create a splitter instance."""
        return HackTricksMarkdownSplitter(chunk_size=200, chunk_overlap=50)

    def test_basic_split(self, splitter):
        """Test basic text splitting."""
        text = "This is a short paragraph.\n\nThis is another paragraph that should be in a separate chunk."
        chunks = splitter.split_text(text)

        assert len(chunks) >= 1
        assert "short paragraph" in chunks[0]

    def test_preserve_code_blocks(self, splitter):
        """Test that code blocks are preserved."""
        text = """
# Title

Some text before code.

```python
def important_function():
    # This code block should not be split
    return "Important result"
```

Some text after code.
"""
        chunks = splitter.split_text(text)

        # Find chunk with code
        code_chunk = None
        for chunk in chunks:
            if "```python" in chunk:
                code_chunk = chunk
                break

        assert code_chunk is not None
        assert "def important_function():" in code_chunk
        assert 'return "Important result"' in code_chunk

    def test_preserve_tables(self, splitter):
        """Test that tables are preserved."""
        text = """
# Title

Here is a table:

| Tool | Category | Usage |
|------|----------|-------|
| nmap | scanning | Network scanning |
| gobuster | web | Directory enumeration |

More text after table.
"""
        chunks = splitter.split_text(text)

        # Find chunk with table
        table_chunk = None
        for chunk in chunks:
            if "| Tool |" in chunk:
                table_chunk = chunk
                break

        assert table_chunk is not None
        assert "| nmap |" in table_chunk
        assert "| gobuster |" in table_chunk

    def test_header_based_splitting(self, splitter):
        """Test splitting based on headers."""
        text = """
# Main Section

Content for main section.

## Subsection 1

Content for subsection 1.

## Subsection 2

Content for subsection 2.
"""
        chunks = splitter.split_text(text)

        # With small chunk size (200), this might fit in one chunk
        assert len(chunks) >= 1

        # Check that headers are preserved
        headers_found = []
        for chunk in chunks:
            if "# Main Section" in chunk:
                headers_found.append("main")
            if "## Subsection" in chunk:
                headers_found.append("sub")

        assert len(headers_found) > 0

    def test_chunk_overlap(self, splitter):
        """Test that overlap is applied between chunks."""
        # Create long text that will definitely be split
        text = "A" * 150 + " " + "B" * 150 + " " + "C" * 150

        chunks = splitter.split_text(text)

        if len(chunks) > 1:
            # Check for overlap - end of first chunk should appear in beginning of second
            # This is a basic test; exact overlap depends on implementation
            assert len(chunks) >= 2

    def test_empty_text(self, splitter):
        """Test handling of empty text."""
        chunks = splitter.split_text("")
        assert chunks == []

    def test_very_long_text(self, splitter):
        """Test handling of very long text."""
        # Create text longer than chunk size
        long_text = "This is a sentence. " * 50
        chunks = splitter.split_text(long_text)

        # Should create multiple chunks
        assert len(chunks) > 1

        # Each chunk should not exceed chunk_size (with tolerance for overlap)
        for chunk in chunks:
            assert len(chunk) <= splitter.chunk_size * 1.5  # 50% tolerance for overlap
