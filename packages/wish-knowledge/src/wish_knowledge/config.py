"""Configuration for knowledge base."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class EmbeddingConfig:
    """Configuration for embedding models."""

    provider: str = "openai"  # "openai" or "local"
    model: str = "text-embedding-3-large"  # Default to high-quality model
    api_key: str | None = field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    dimension: int = 3072  # For text-embedding-3-large
    batch_size: int = 100


@dataclass
class HackTricksConfig:
    """Configuration for HackTricks source."""

    repo_url: str = "https://github.com/HackTricks-wiki/hacktricks"
    enabled: bool = True
    clone_depth: int = 1
    chunk_size: int = 1000  # Reduced for safer token limits
    chunk_overlap: int = 200  # Adjusted proportionally


@dataclass
class StorageConfig:
    """Configuration for storage."""

    base_path: Path = field(default_factory=lambda: Path.home() / ".wish" / "knowledge_base")
    chromadb_path: str = "chromadb"
    metadata_filename: str = "metadata.json"
    cache_dir: str = "cache"


@dataclass
class KnowledgeConfig:
    """Main knowledge base configuration."""

    auto_import: bool = True
    update_interval_days: int = 30
    sources: list[str] = field(default_factory=lambda: ["hacktricks"])

    # Sub-configurations
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    hacktricks: HackTricksConfig = field(default_factory=HackTricksConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)

    # Runtime settings
    progress_callback: Any | None = None  # Callback for progress updates

    def __post_init__(self) -> None:
        """Ensure storage directories exist."""
        self.storage.base_path.mkdir(parents=True, exist_ok=True)
        (self.storage.base_path / self.storage.chromadb_path).mkdir(exist_ok=True)
        (self.storage.base_path / self.storage.cache_dir).mkdir(exist_ok=True)

    def get_chromadb_path(self) -> Path:
        """Get full path to ChromaDB directory."""
        return self.storage.base_path / self.storage.chromadb_path

    def get_metadata_path(self) -> Path:
        """Get full path to metadata JSON file."""
        return self.storage.base_path / self.storage.metadata_filename

    def get_cache_path(self) -> Path:
        """Get full path to cache directory."""
        return self.storage.base_path / self.storage.cache_dir
