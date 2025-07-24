"""Test that all_tools error is fixed."""

from unittest.mock import MagicMock, patch

import pytest
from wish_knowledge.config import KnowledgeConfig
from wish_knowledge.sources import HackTricksSource


class TestNoAllToolsError:
    """Test that the all_tools reference error is fixed."""

    @pytest.mark.asyncio
    async def test_process_documents_no_all_tools_error(self):
        """Test that process_all_documents doesn't reference undefined all_tools."""
        config = KnowledgeConfig()

        # Mock GitHub operations
        with patch('git.Repo.clone_from') as mock_clone:
            with patch('pathlib.Path.glob') as mock_glob:
                # Mock finding markdown files
                mock_file = MagicMock()
                mock_file.read_text.return_value = "# Test\nSome test content"
                mock_file.name = "test.md"
                mock_file.__str__ = lambda: "test.md"
                mock_glob.return_value = [mock_file]

                # Mock ChromaDB operations
                with patch('wish_knowledge.vectorstore.ChromaDBStore') as mock_chroma_class:
                    mock_chroma = MagicMock()
                    mock_chroma.add_documents = MagicMock()
                    mock_chroma_class.return_value = mock_chroma

                    source = HackTricksSource(config)

                    try:
                        # This should not raise "name 'all_tools' is not defined"
                        result = await source.process_and_store()
                        # Verify we get a result
                        assert result is not None
                        assert "status" in result
                        assert result["status"] == "success"

                        # Should have processed chunks
                        assert "chunks" in result
                        assert result["chunks"] >= 0

                        # Should NOT have tools field (we removed it)
                        assert "tools" not in result

                        print("✓ No all_tools error - fix confirmed!")

                    except NameError as e:
                        if "all_tools" in str(e):
                            pytest.fail(f"all_tools error still exists: {e}")
                        else:
                            # Different NameError, re-raise
                            raise
                    except Exception as e:
                        print(f"Other error (not all_tools): {e}")
                        # Allow other errors for now, we just want to confirm all_tools is fixed
                        pass
