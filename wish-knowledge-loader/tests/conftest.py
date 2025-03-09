"""Test configuration for wish-knowledge-loader."""

import os

import pytest

# Set environment variables for testing
os.environ["OPENAI_API_KEY"] = "sk-test-key"
os.environ["OPENAI_MODEL"] = "text-embedding-3-small"
os.environ["WISH_HOME"] = "/tmp/wish-test"
os.environ["LANGCHAIN_API_KEY"] = "ls-test-key"
os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_PROJECT"] = "wish-test"

@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch, tmp_path):
    """Set up test environment."""
    # Create temporary directories
    knowledge_dir = tmp_path / "knowledge"
    knowledge_dir.mkdir(exist_ok=True)
    repo_dir = knowledge_dir / "repo"
    repo_dir.mkdir(exist_ok=True)
    db_dir = knowledge_dir / "db"
    db_dir.mkdir(exist_ok=True)

    # Set WISH_HOME to point to the temporary directory
    monkeypatch.setenv("WISH_HOME", str(tmp_path))

    yield
