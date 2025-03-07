"""Debug tests for wish-knowledge-loader."""

import os
from pathlib import Path

import pytest

from wish_knowledge_loader.nodes.document_loader import DocumentLoader
from wish_knowledge_loader.nodes.repo_cloner import RepoCloner
from wish_knowledge_loader.nodes.vector_store import VectorStore
from wish_knowledge_loader.settings import Settings


class TestDebug:
    """Debug tests for wish-knowledge-loader."""

    @pytest.mark.skip(reason="Debug test - only run manually")
    def test_settings_load(self):
        """Test loading settings from environment variables.

        TODO Remove this test (for debugging)
        """
        # Set environment variables
        os.environ["WISH_HOME"] = "/tmp/wish_home"
        os.environ["OPENAI_API_KEY"] = "test-api-key"

        # Load settings
        settings = Settings()

        # Check if settings were loaded correctly
        assert settings.WISH_HOME == "/tmp/wish_home"
        assert settings.OPENAI_API_KEY == "test-api-key"
        assert settings.OPENAI_MODEL == "text-embedding-3-small"

        # Check if paths are correct
        assert settings.knowledge_dir == Path("/tmp/wish_home/knowledge")
        assert settings.repo_dir == Path("/tmp/wish_home/knowledge/repo")
        assert settings.db_dir == Path("/tmp/wish_home/knowledge/db")
        assert settings.meta_path == Path("/tmp/wish_home/knowledge/meta.json")

    @pytest.mark.skip(reason="Debug test - only run manually")
    def test_repo_cloner(self):
        """Test cloning a repository.

        TODO Remove this test (for debugging)
        """
        # Set environment variables
        os.environ["WISH_HOME"] = "/tmp/wish_home"

        # Load settings
        settings = Settings()

        # Create RepoCloner
        repo_cloner = RepoCloner(settings)

        # Clone repository
        repo_url = "https://github.com/langchain-ai/langchain"
        repo_path = repo_cloner.clone(repo_url)

        # Check if repository was cloned
        assert repo_path.exists()
        assert (repo_path / ".git").exists()

    @pytest.mark.skip(reason="Debug test - only run manually")
    def test_document_loader(self):
        """Test loading documents from a repository.

        TODO Remove this test (for debugging)
        """
        # Set environment variables
        os.environ["WISH_HOME"] = "/tmp/wish_home"

        # Load settings
        settings = Settings()

        # Create DocumentLoader
        document_loader = DocumentLoader(settings)

        # Load documents
        repo_path = Path("/tmp/wish_home/knowledge/repo/github.com/langchain-ai/langchain")
        glob_pattern = "**/*.md"
        documents = document_loader.load(repo_path, glob_pattern)

        # Check if documents were loaded
        assert len(documents) > 0

        # Split documents
        chunk_size = 1000
        chunk_overlap = 100
        split_docs = document_loader.split(documents, chunk_size, chunk_overlap)

        # Check if documents were split
        assert len(split_docs) >= len(documents)

    @pytest.mark.skip(reason="Debug test - only run manually")
    def test_vector_store(self):
        """Test storing documents in a vector store.

        TODO Remove this test (for debugging)
        """
        # Set environment variables
        os.environ["WISH_HOME"] = "/tmp/wish_home"
        os.environ["OPENAI_API_KEY"] = "your-api-key-here"

        # Load settings
        settings = Settings()

        # Create DocumentLoader
        document_loader = DocumentLoader(settings)

        # Load documents
        repo_path = Path("/tmp/wish_home/knowledge/repo/github.com/langchain-ai/langchain")
        glob_pattern = "**/*.md"
        documents = document_loader.load(repo_path, glob_pattern)

        # Split documents
        chunk_size = 1000
        chunk_overlap = 100
        # Use only 10 documents for testing
        split_docs = document_loader.split(documents[:10], chunk_size, chunk_overlap)

        # Create VectorStore
        vector_store = VectorStore(settings)

        # Store documents
        title = "LangChain"
        vector_store.store(title, split_docs)

        # Check if vector store was created
        db_path = settings.db_dir / title
        assert db_path.exists()
