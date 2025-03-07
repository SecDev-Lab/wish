"""Integration tests for wish-knowledge-loader."""

import json
import os
import shutil
import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner
from wish_models.knowledge.knowledge_metadata import KnowledgeMetadataContainer

from wish_knowledge_loader.cli import main


class TestIntegration:
    """Integration test for wish-knowledge-loader."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def mock_repo(self, temp_dir):
        """Create a mock repository."""
        repo_dir = Path(temp_dir) / "mock_repo"
        repo_dir.mkdir(parents=True)

        # Create a .git directory to simulate a git repository
        git_dir = repo_dir / ".git"
        git_dir.mkdir()

        # Create some markdown files
        docs_dir = repo_dir / "docs"
        docs_dir.mkdir()

        with open(docs_dir / "file1.md", "w") as f:
            f.write("# Test File 1\n\nThis is a test file.")

        with open(docs_dir / "file2.md", "w") as f:
            f.write("# Test File 2\n\nThis is another test file.")

        # Create a non-markdown file
        with open(docs_dir / "file3.txt", "w") as f:
            f.write("This is not a markdown file.")

        return repo_dir

    @pytest.fixture
    def env_vars(self, temp_dir):
        """Set environment variables for testing."""
        old_env = os.environ.copy()

        # Set environment variables
        os.environ["WISH_HOME"] = str(Path(temp_dir) / "wish_home")
        os.environ["OPENAI_API_KEY"] = "test-api-key"
        os.environ["OPENAI_MODEL"] = "text-embedding-3-small"

        yield

        # Restore environment variables
        os.environ.clear()
        os.environ.update(old_env)

    @pytest.mark.skip(reason="This test requires a real git repository and OpenAI API key")
    def test_end_to_end(self, temp_dir, mock_repo, env_vars):
        """Test the entire workflow from end to end."""
        # Create a runner
        runner = CliRunner()

        # Run the CLI
        result = runner.invoke(main, [
            "--repo-url", str(mock_repo),
            "--glob", "**/*.md",
            "--title", "Test Knowledge"
        ])

        # Check if the command was successful
        assert result.exit_code == 0
        assert "Successfully loaded knowledge base: Test Knowledge" in result.output

        # Check if the metadata file was created
        wish_home = Path(os.environ["WISH_HOME"])
        meta_path = wish_home / "knowledge" / "meta.json"
        assert meta_path.exists()

        # Check if the metadata contains the correct information
        with open(meta_path, "r") as f:
            meta_data = json.load(f)

        container = KnowledgeMetadataContainer.from_dict(meta_data)
        metadata = container.get("Test Knowledge")

        assert metadata is not None
        assert metadata.title == "Test Knowledge"
        assert metadata.repo_url == str(mock_repo)
        assert metadata.glob_pattern == "**/*.md"

        # Check if the vector database was created
        db_dir = wish_home / "knowledge" / "db" / "Test Knowledge"
        assert db_dir.exists()
