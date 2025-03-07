"""Tests for CLI functionality."""

from pathlib import Path
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

import pytest

from wish_knowledge_loader.cli import main
from wish_knowledge_loader.models.knowledge_metadata import KnowledgeMetadata, KnowledgeMetadataContainer
from wish_knowledge_loader.nodes.repo_cloner import RepoCloner
from wish_knowledge_loader.nodes.document_loader import DocumentLoader
from wish_knowledge_loader.nodes.vector_store import VectorStore
from wish_knowledge_loader.settings import Settings
from wish_models.utc_datetime import UtcDatetime


class TestCli:
    """Test for CLI."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    @patch("wish_knowledge_loader.cli.Settings")
    @patch("wish_knowledge_loader.cli.KnowledgeMetadataContainer")
    @patch("wish_knowledge_loader.cli.RepoCloner")
    @patch("wish_knowledge_loader.cli.DocumentLoader")
    @patch("wish_knowledge_loader.cli.VectorStore")
    @patch("wish_knowledge_loader.cli.UtcDatetime")
    def test_main_success(self, mock_utc_datetime, mock_vector_store, mock_document_loader,
                          mock_repo_cloner, mock_container, mock_settings, runner):
        """Test successful execution of the CLI."""
        # Set up mocks
        mock_settings_instance = MagicMock(spec=Settings)
        mock_settings.return_value = mock_settings_instance
        mock_settings_instance.meta_path = Path("/tmp/meta.json")

        mock_container_instance = MagicMock(spec=KnowledgeMetadataContainer)
        mock_container.load.return_value = mock_container_instance

        mock_repo_cloner_instance = MagicMock(spec=RepoCloner)
        mock_repo_cloner.return_value = mock_repo_cloner_instance
        mock_repo_cloner_instance.clone.return_value = Path("/tmp/repo")

        mock_document_loader_instance = MagicMock(spec=DocumentLoader)
        mock_document_loader.return_value = mock_document_loader_instance
        mock_document_loader_instance.load.return_value = ["doc1", "doc2"]
        mock_document_loader_instance.split.return_value = ["split_doc1", "split_doc2"]

        mock_vector_store_instance = MagicMock(spec=VectorStore)
        mock_vector_store.return_value = mock_vector_store_instance

        mock_utc_datetime_instance = MagicMock()
        mock_utc_datetime.now.return_value = mock_utc_datetime_instance

        # Run CLI
        result = runner.invoke(main, [
            "--repo-url", "https://github.com/test/repo",
            "--glob", "**/*.md",
            "--title", "Test Knowledge"
        ])

        # Check if the command was successful
        assert result.exit_code == 0
        assert "Successfully loaded knowledge base: Test Knowledge" in result.output

        # Check if the mocks were called with correct arguments
        mock_settings.assert_called_once()
        mock_container.load.assert_called_once_with(mock_settings_instance.meta_path)

        mock_repo_cloner.assert_called_once_with(mock_settings_instance)
        mock_repo_cloner_instance.clone.assert_called_once_with("https://github.com/test/repo")

        mock_document_loader.assert_called_once_with(mock_settings_instance)
        mock_document_loader_instance.load.assert_called_once_with(Path("/tmp/repo"), "**/*.md")
        mock_document_loader_instance.split.assert_called_once_with(["doc1", "doc2"], 1000, 100)

        mock_vector_store.assert_called_once_with(mock_settings_instance)
        mock_vector_store_instance.store.assert_called_once_with("Test Knowledge", ["split_doc1", "split_doc2"])

        mock_container_instance.add.assert_called_once()
        mock_container_instance.save.assert_called_once_with(mock_settings_instance.meta_path)

    @patch("wish_knowledge_loader.cli.Settings")
    def test_main_error(self, mock_settings, runner):
        """Test error handling in the CLI."""
        # Set up mock to raise an exception
        mock_settings.side_effect = Exception("Test error")

        # Run CLI
        result = runner.invoke(main, [
            "--repo-url", "https://github.com/test/repo",
            "--glob", "**/*.md",
            "--title", "Test Knowledge"
        ])

        # Check if the command failed
        assert result.exit_code == 1
        assert "Error: Test error" in result.output
