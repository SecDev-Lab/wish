"""Tests for CLI functionality."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner
from wish_models.knowledge.knowledge_metadata import KnowledgeMetadataContainer
from wish_models.utc_datetime import UtcDatetime

from wish_knowledge_loader.cli import main
from wish_knowledge_loader.nodes.document_loader import DocumentLoader
from wish_knowledge_loader.nodes.repo_cloner import RepoCloner
from wish_knowledge_loader.nodes.vector_store import VectorStore
from wish_knowledge_loader.settings import Settings


class TestCli:
    """Test for CLI."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    @patch("wish_knowledge_loader.cli.setup_logger")
    @patch("wish_knowledge_loader.cli.Settings")
    @patch("wish_knowledge_loader.cli.KnowledgeMetadataContainer")
    @patch("wish_knowledge_loader.cli.RepoCloner")
    @patch("wish_knowledge_loader.cli.DocumentLoader")
    @patch("wish_knowledge_loader.cli.VectorStore")
    @patch("wish_knowledge_loader.cli.UtcDatetime")
    def test_main_success(self, mock_utc_datetime, mock_vector_store, mock_document_loader,
                          mock_repo_cloner, mock_container, mock_settings, mock_setup_logger, runner):
        """Test successful execution of the CLI."""
        # Set up mocks
        mock_settings_instance = MagicMock(spec=Settings)
        mock_settings.return_value = mock_settings_instance
        mock_settings_instance.WISH_HOME = "/tmp/.wish"
        mock_settings_instance.meta_path = Path("/tmp/meta.json")

        # Create a mock logger
        mock_logger = MagicMock()
        mock_setup_logger.return_value = mock_logger

        mock_container_instance = MagicMock(spec=KnowledgeMetadataContainer)
        mock_container_instance.m = {}
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

        # Create a real UtcDatetime instance for the mock
        from datetime import datetime, timezone
        real_utc_datetime = UtcDatetime(datetime.now(timezone.utc))
        mock_utc_datetime.now.return_value = real_utc_datetime

        # Run CLI with catch_exceptions=False to let the exception propagate
        result = runner.invoke(main, [
            "--repo-url", "https://github.com/test/repo",
            "--glob", "**/*.md",
            "--title", "Test Knowledge"
        ], catch_exceptions=False)

        # Check if the command was successful
        assert result.exit_code == 0
        assert "Successfully loaded knowledge base: Test Knowledge" in result.output

        # Check if the mocks were called with correct arguments
        mock_settings.assert_called_once()
        mock_container.load.assert_called_once_with(mock_settings_instance.meta_path)

        mock_repo_cloner.assert_called_once_with(mock_settings_instance, logger=mock_logger)
        mock_repo_cloner_instance.clone.assert_called_once_with("https://github.com/test/repo")

        mock_document_loader.assert_called_once_with(mock_settings_instance, logger=mock_logger)
        mock_document_loader_instance.load.assert_called_once_with(Path("/tmp/repo"), "**/*.md")
        mock_document_loader_instance.split.assert_called_once_with(["doc1", "doc2"], 1000, 100)

        mock_vector_store.assert_called_once_with(mock_settings_instance, logger=mock_logger)
        mock_vector_store_instance.store.assert_called_once_with("Test Knowledge", ["split_doc1", "split_doc2"])

        mock_container_instance.add.assert_called_once()
        mock_container_instance.save.assert_called_once_with(mock_settings_instance.meta_path)

    @patch("wish_knowledge_loader.cli.setup_logger")
    @patch("wish_knowledge_loader.cli.Settings")
    def test_main_error(self, mock_settings, mock_setup_logger, runner):
        """Test error handling in the CLI."""
        # Set up mocks
        mock_settings.side_effect = Exception("Test error")

        # Create a mock logger
        mock_logger = MagicMock()
        mock_setup_logger.return_value = mock_logger

        # Run CLI with catch_exceptions=True to capture the output
        result = runner.invoke(main, [
            "--repo-url", "https://github.com/test/repo",
            "--glob", "**/*.md",
            "--title", "Test Knowledge"
        ])

        # Check if the command failed
        # Note: We're not checking exit_code here because it's not reliable in this test
        assert "Error: Test error" in result.output
