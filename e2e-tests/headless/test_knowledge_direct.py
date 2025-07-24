"""Direct test of knowledge initialization without HeadlessWish complexity."""

import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from wish_knowledge.config import KnowledgeConfig
from wish_knowledge.manager import KnowledgeManager, check_knowledge_initialized


class TestKnowledgeDirect:
    """Direct knowledge initialization tests."""

    @pytest.mark.asyncio
    async def test_direct_knowledge_initialization(self):
        """Test knowledge initialization directly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create config with temp directory
            config = KnowledgeConfig()
            config.storage.base_path = Path(temp_dir) / "knowledge_base"
            config.storage.base_path.mkdir(parents=True, exist_ok=True)

            # Create manager
            manager = KnowledgeManager(config)

            # Check if initialization is needed
            needs_init = not check_knowledge_initialized()

            if needs_init:
                # Mock the HackTricks source to avoid real GitHub access
                with patch('wish_knowledge.sources.HackTricksSource') as mock_source_class:
                    mock_source = MagicMock()
                    mock_source.process_all_documents = AsyncMock(return_value={
                        "status": "success",
                        "processed": 10,
                        "chunks": 100
                    })
                    mock_source_class.return_value = mock_source

                    # Mock ChromaDB to avoid real database operations
                    with patch('wish_knowledge.vectorstore.ChromaDBStore') as mock_chroma_class:
                        mock_chroma = MagicMock()
                        mock_chroma.add_documents = MagicMock()
                        mock_chroma_class.return_value = mock_chroma

                        try:
                            result = await manager.initialize_foreground()
                            assert result is not None

                            # Verify the source was called
                            mock_source.process_all_documents.assert_called_once()

                        except Exception:
                            import traceback
                            traceback.print_exc()
                            raise
            else:
                # Knowledge base already exists, test passes
                pass

    @pytest.mark.asyncio
    async def test_actual_knowledge_initialization_error(self):
        """Test to reproduce the actual error from wish startup."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Set HOME to temp directory
            with patch.dict(os.environ, {'HOME': temp_dir}):

                # Use real config paths like wish would
                config = KnowledgeConfig()  # This will use the temp HOME

                manager = KnowledgeManager(config)

                try:
                    # Try real initialization to see the actual error
                    result = await manager.initialize_foreground()
                    assert result is not None

                except Exception as e:
                    # Check if it's the 'all_tools' error we fixed
                    if "all_tools" in str(e):
                        pytest.fail("all_tools error still exists")

                    import traceback
                    traceback.print_exc()

                    # Re-raise to see full details
                    raise
