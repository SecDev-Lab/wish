"""Tests for knowledge base configuration."""

from wish_knowledge.config import EmbeddingConfig, HackTricksConfig, KnowledgeConfig


class TestKnowledgeConfig:
    """Test KnowledgeConfig functionality."""

    def test_default_config(self, tmp_path, monkeypatch):
        """Test default configuration values."""
        # Set HOME to temp directory
        monkeypatch.setenv("HOME", str(tmp_path))

        config = KnowledgeConfig()

        assert config.auto_import is True
        assert config.update_interval_days == 30
        assert config.sources == ["hacktricks"]
        assert config.embedding.provider == "openai"
        assert config.embedding.model == "text-embedding-3-large"
        assert config.embedding.dimension == 3072

    def test_storage_paths_creation(self, tmp_path, monkeypatch):
        """Test that storage directories are created."""
        # Set HOME to temp directory
        monkeypatch.setenv("HOME", str(tmp_path))

        config = KnowledgeConfig()

        # Check that directories exist
        assert config.storage.base_path.exists()
        assert config.get_chromadb_path().exists()
        assert config.get_cache_path().exists()

    def test_path_methods(self, tmp_path, monkeypatch):
        """Test path getter methods."""
        monkeypatch.setenv("HOME", str(tmp_path))

        config = KnowledgeConfig()
        base_path = tmp_path / ".wish" / "knowledge_base"

        assert config.get_chromadb_path() == base_path / "chromadb"
        assert config.get_metadata_path() == base_path / "metadata.json"
        assert config.get_cache_path() == base_path / "cache"


class TestEmbeddingConfig:
    """Test EmbeddingConfig functionality."""

    def test_default_embedding_config(self):
        """Test default embedding configuration."""
        config = EmbeddingConfig()

        assert config.provider == "openai"
        assert config.model == "text-embedding-3-large"
        assert config.dimension == 3072
        assert config.batch_size == 100

    def test_api_key_from_env(self, monkeypatch):
        """Test API key loading from environment."""
        test_key = "sk-test-key-123"
        monkeypatch.setenv("OPENAI_API_KEY", test_key)

        config = EmbeddingConfig()
        assert config.api_key == test_key


class TestHackTricksConfig:
    """Test HackTricksConfig functionality."""

    def test_default_hacktricks_config(self):
        """Test default HackTricks configuration."""
        config = HackTricksConfig()

        assert config.repo_url == "https://github.com/HackTricks-wiki/hacktricks"
        assert config.enabled is True
        assert config.clone_depth == 1
        assert config.chunk_size == 1000
        assert config.chunk_overlap == 200
