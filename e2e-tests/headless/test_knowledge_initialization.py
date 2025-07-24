"""Test HackTricks knowledge base initialization using HeadlessWish."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from wish_cli.headless import EventType, HeadlessWish
from wish_knowledge.config import KnowledgeConfig


class TestKnowledgeInitialization:
    """Test HackTricks knowledge base initialization through HeadlessWish."""

    @pytest.fixture
    def isolated_wish_config(self):
        """Create isolated wish config directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock the config path to use temp directory
            with patch('wish_cli.config.get_config_dir', return_value=Path(temp_dir)):
                with patch('wish_knowledge.config.KnowledgeConfig') as mock_config_class:
                    # Create mock config instance
                    mock_config = MagicMock(spec=KnowledgeConfig)
                    mock_config.storage.base_path = Path(temp_dir) / "knowledge_base"
                    mock_config.storage.base_path.mkdir(parents=True, exist_ok=True)
                    mock_config.get_chromadb_path.return_value = mock_config.storage.base_path / "chromadb"
                    mock_config.get_metadata_path.return_value = mock_config.storage.base_path / "metadata.json"
                    mock_config.get_cache_path.return_value = mock_config.storage.base_path / "cache"
                    mock_config_class.return_value = mock_config

                    yield temp_dir, mock_config

    @pytest.mark.asyncio
    async def test_successful_knowledge_initialization(self, isolated_wish_config):
        """Test successful HackTricks knowledge base initialization."""
        temp_dir, mock_config = isolated_wish_config

        # Track initialization progress
        progress_events = []
        initialization_complete = False

        # Mock successful HackTricks source processing
        with patch('wish_knowledge.sources.HackTricksSource') as mock_source_class:
            mock_source = MagicMock()
            mock_source.process_all_documents = AsyncMock(return_value={
                "status": "success",
                "processed": 150,
                "chunks": 3250
            })
            mock_source_class.return_value = mock_source

            # Mock ChromaDB operations
            with patch('wish_knowledge.vectorstore.ChromaDBStore') as mock_chroma_class:
                mock_chroma = MagicMock()
                mock_chroma.add_documents = MagicMock()
                mock_chroma_class.return_value = mock_chroma

                # Create HeadlessWish instance
                wish = HeadlessWish(auto_approve=True)

                @wish.on_event(EventType.INITIALIZATION_PROGRESS)
                async def track_progress(event):
                    progress_events.append(event.data)

                @wish.on_event(EventType.INITIALIZATION_COMPLETE)
                async def track_completion(event):
                    nonlocal initialization_complete
                    initialization_complete = True

                # Start session (this should trigger knowledge initialization)
                session = await wish.start_session()

                try:
                    # Give some time for initialization to complete
                    import asyncio
                    await asyncio.sleep(0.5)

                    # Verify initialization was attempted
                    mock_source.process_all_documents.assert_called_once()

                    # Verify progress was tracked
                    assert len(progress_events) > 0, "Expected progress events during initialization"

                    # Test a simple query to ensure system is functional
                    result = await session.send_prompt("test query")
                    assert result.result is not None

                finally:
                    await session.end()

    @pytest.mark.asyncio
    async def test_knowledge_initialization_failure_handling(self, isolated_wish_config):
        """Test graceful handling of knowledge initialization failures."""
        temp_dir, mock_config = isolated_wish_config

        initialization_failed = False
        error_message = None

        # Mock failed HackTricks source processing
        with patch('wish_knowledge.sources.HackTricksSource') as mock_source_class:
            mock_source = MagicMock()
            mock_source.process_all_documents = AsyncMock(side_effect=Exception("Mock initialization error"))
            mock_source_class.return_value = mock_source

            wish = HeadlessWish(auto_approve=True)

            @wish.on_event(EventType.INITIALIZATION_ERROR)
            async def track_error(event):
                nonlocal initialization_failed, error_message
                initialization_failed = True
                error_message = str(event.data)

            session = await wish.start_session()

            try:
                # Give time for initialization attempt
                import asyncio
                await asyncio.sleep(0.5)

                # System should still be functional even if knowledge init failed
                result = await session.send_prompt("test query after failed init")
                assert result.result is not None, "System should remain functional after knowledge init failure"

                # Verify error was properly handled
                mock_source.process_all_documents.assert_called_once()

            finally:
                await session.end()

    @pytest.mark.asyncio
    async def test_skip_initialization_when_already_exists(self, isolated_wish_config):
        """Test that initialization is skipped when knowledge base already exists."""
        temp_dir, mock_config = isolated_wish_config

        # Create fake existing knowledge base
        kb_path = Path(temp_dir) / "knowledge_base"
        kb_path.mkdir(exist_ok=True)
        metadata_path = kb_path / "metadata.json"
        metadata_path.write_text('{"last_updated": "2024-01-01T00:00:00"}')

        initialization_attempted = False

        with patch('wish_knowledge.sources.HackTricksSource') as mock_source_class:
            mock_source = MagicMock()
            mock_source.process_all_documents = AsyncMock(return_value={
                "status": "success",
                "processed": 0,
                "chunks": 0
            })
            mock_source_class.return_value = mock_source

            # Mock the check for existing knowledge base
            with patch('wish_knowledge.manager.check_knowledge_initialized', return_value=True):
                wish = HeadlessWish(auto_approve=True)

                @wish.on_event(EventType.INITIALIZATION_PROGRESS)
                async def track_initialization(event):
                    nonlocal initialization_attempted
                    initialization_attempted = True

                session = await wish.start_session()

                try:
                    import asyncio
                    await asyncio.sleep(0.5)

                    # Verify initialization was NOT attempted
                    mock_source.process_all_documents.assert_not_called()
                    assert not initialization_attempted, "Initialization should be skipped when knowledge base exists"

                    # System should still work
                    result = await session.send_prompt("test query with existing kb")
                    assert result.result is not None

                finally:
                    await session.end()

    @pytest.mark.asyncio
    async def test_knowledge_search_functionality(self, isolated_wish_config):
        """Test that knowledge search works after initialization."""
        temp_dir, mock_config = isolated_wish_config

        # Mock successful initialization and search
        mock_search_results = [
            {
                "content": "nmap -sV -sC target.com",
                "metadata": {"source": "hacktricks", "category": "reconnaissance"},
                "score": 0.95
            },
            {
                "content": "SMB enumeration techniques using enum4linux",
                "metadata": {"source": "hacktricks", "category": "enumeration"},
                "score": 0.87
            }
        ]

        with patch('wish_knowledge.sources.HackTricksSource') as mock_source_class:
            mock_source = MagicMock()
            mock_source.process_all_documents = AsyncMock(return_value={
                "status": "success",
                "processed": 100,
                "chunks": 2000
            })
            mock_source_class.return_value = mock_source

            # Mock the retriever search functionality
            with patch('wish_knowledge.sources.HackTricksRetriever') as mock_retriever_class:
                mock_retriever = MagicMock()
                mock_retriever.search = AsyncMock(return_value=mock_search_results)
                mock_retriever_class.return_value = mock_retriever

                wish = HeadlessWish(auto_approve=True)
                session = await wish.start_session()

                try:
                    # Give time for initialization
                    import asyncio
                    await asyncio.sleep(0.5)

                    # Test knowledge-based query
                    result = await session.send_prompt("How do I scan for open ports using nmap?")

                    # Verify response contains relevant information
                    assert result.result is not None
                    response_text = result.result.lower()

                    # Response should contain scanning-related content
                    scan_keywords = ["nmap", "scan", "port", "reconnaissance"]
                    found_keywords = [kw for kw in scan_keywords if kw in response_text]
                    assert len(found_keywords) >= 2, f"Expected scanning-related content, found keywords: {found_keywords}"

                finally:
                    await session.end()
