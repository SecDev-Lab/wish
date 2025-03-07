"""Tests for document loading functionality."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from langchain.schema import Document

from wish_knowledge_loader.nodes.document_loader import DocumentLoader
from wish_knowledge_loader.settings import Settings


class TestDocumentLoader:
    """Test for DocumentLoader."""

    @pytest.fixture
    def settings(self):
        """Create test settings."""
        return MagicMock(spec=Settings)

    @patch("wish_knowledge_loader.nodes.document_loader.DirectoryLoader")
    def test_load(self, mock_directory_loader, settings):
        """Test loading documents."""
        # Create DocumentLoader instance
        document_loader = DocumentLoader(settings)

        # Set up mock
        mock_loader = MagicMock()
        mock_directory_loader.return_value = mock_loader
        mock_loader.load.return_value = [
            Document(page_content="Test content 1", metadata={"source": "test1.md"}),
            Document(page_content="Test content 2", metadata={"source": "test2.md"})
        ]

        # Call load method
        repo_path = Path("/tmp/test")
        glob_pattern = "**/*.md"
        documents = document_loader.load(repo_path, glob_pattern)

        # Check if DirectoryLoader was created with correct arguments
        mock_directory_loader.assert_called_once_with(
            str(repo_path),
            glob=glob_pattern,
            loader_cls=document_loader.TextLoader
        )

        # Check if load method was called
        mock_loader.load.assert_called_once()

        # Check if documents were returned
        assert len(documents) == 2
        assert documents[0].page_content == "Test content 1"
        assert documents[1].page_content == "Test content 2"

    @patch("wish_knowledge_loader.nodes.document_loader.RecursiveCharacterTextSplitter")
    def test_split(self, mock_text_splitter, settings):
        """Test splitting documents."""
        # Create DocumentLoader instance
        document_loader = DocumentLoader(settings)

        # Set up mock
        mock_splitter = MagicMock()
        mock_text_splitter.return_value = mock_splitter
        mock_splitter.split_documents.return_value = [
            Document(page_content="Test content 1a", metadata={"source": "test1.md"}),
            Document(page_content="Test content 1b", metadata={"source": "test1.md"}),
            Document(page_content="Test content 2a", metadata={"source": "test2.md"}),
            Document(page_content="Test content 2b", metadata={"source": "test2.md"})
        ]

        # Create test documents
        documents = [
            Document(page_content="Test content 1", metadata={"source": "test1.md"}),
            Document(page_content="Test content 2", metadata={"source": "test2.md"})
        ]

        # Call split method
        chunk_size = 1000
        chunk_overlap = 100
        split_docs = document_loader.split(documents, chunk_size, chunk_overlap)

        # Check if RecursiveCharacterTextSplitter was created with correct arguments
        mock_text_splitter.assert_called_once_with(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

        # Check if split_documents method was called with correct arguments
        mock_splitter.split_documents.assert_called_once_with(documents)

        # Check if split documents were returned
        assert len(split_docs) == 4
        assert split_docs[0].page_content == "Test content 1a"
        assert split_docs[1].page_content == "Test content 1b"
        assert split_docs[2].page_content == "Test content 2a"
        assert split_docs[3].page_content == "Test content 2b"
