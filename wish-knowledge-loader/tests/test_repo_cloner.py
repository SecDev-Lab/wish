"""Tests for repository cloning functionality."""

from unittest.mock import MagicMock, patch

import pytest
from wish_models.settings import Settings

from wish_knowledge_loader.nodes.repo_cloner import RepoCloner


class TestRepoCloner:
    """Test for RepoCloner."""

    @pytest.fixture
    def settings(self, tmp_path):
        """Create test settings."""
        settings = MagicMock(spec=Settings)
        settings.repo_dir = tmp_path / "repo"
        return settings

    @patch("subprocess.run")
    @patch("wish_knowledge_loader.nodes.repo_cloner.Settings", return_value=MagicMock())
    def test_clone_new_repo(self, mock_settings_class, mock_run, settings):
        """Test cloning a new repository."""
        # Set up mock settings
        mock_settings = mock_settings_class.return_value
        mock_settings.repo_dir = settings.repo_dir

        # Create RepoCloner instance
        repo_cloner = RepoCloner(settings)

        # Set up mock
        mock_run.return_value = MagicMock()

        # Call clone method
        repo_url = "https://github.com/test/repo"
        repo_path = repo_cloner.clone(repo_url)

        # Check if the path is correct
        expected_path = settings.repo_dir / "github.com" / "test" / "repo"
        assert repo_path == expected_path

        # Check if subprocess.run was called with correct arguments
        mock_run.assert_called_once_with(
            ["git", "clone", repo_url, str(expected_path)],
            check=True
        )

    @patch("subprocess.run")
    @patch("wish_knowledge_loader.nodes.repo_cloner.Settings", return_value=MagicMock())
    def test_clone_existing_repo(self, mock_settings_class, mock_run, settings):
        """Test cloning an existing repository."""
        # Set up mock settings
        mock_settings = mock_settings_class.return_value
        mock_settings.repo_dir = settings.repo_dir

        # Create RepoCloner instance
        repo_cloner = RepoCloner(settings)

        # Create directory for existing repo
        repo_path = settings.repo_dir / "github.com" / "test" / "repo"
        repo_path.parent.mkdir(parents=True, exist_ok=True)
        repo_path.mkdir(parents=True, exist_ok=True)

        # Set up mock
        mock_run.return_value = MagicMock()

        # Call clone method
        repo_url = "https://github.com/test/repo"
        result_path = repo_cloner.clone(repo_url)

        # Check if the path is correct
        assert result_path == repo_path

        # Check if subprocess.run was called with correct arguments
        mock_run.assert_called_once_with(
            ["git", "-C", str(repo_path), "pull"],
            check=True
        )

    @patch("wish_knowledge_loader.nodes.repo_cloner.Settings", return_value=MagicMock())
    def test_clone_invalid_url(self, mock_settings_class, settings):
        """Test cloning with an invalid URL."""
        # Set up mock settings
        mock_settings = mock_settings_class.return_value
        mock_settings.repo_dir = settings.repo_dir

        # Create RepoCloner instance
        repo_cloner = RepoCloner(settings)

        # Call clone method with invalid URL
        with pytest.raises(ValueError, match="Invalid GitHub URL"):
            repo_cloner.clone("https://github.com/test")
