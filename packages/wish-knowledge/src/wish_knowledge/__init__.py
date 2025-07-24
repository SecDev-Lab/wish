"""
wish-knowledge: RAG and knowledge base integration for wish

This package provides retrieval-augmented generation capabilities and
integration with knowledge sources like HackTricks.
"""

from .config import KnowledgeConfig
from .exceptions import (
    EmbeddingError,
    ExtractionError,
    KnowledgeSourceError,
    StorageError,
    WishKnowledgeError,
)
from .rag import ChromaVectorStore, Retriever, VectorStore
from .sources import HackTricksRetriever, HackTricksSource, KnowledgeSource
from .storage import MetadataStorage
from .vectorstore import ChromaDBStore

__all__ = [
    # Core classes
    "VectorStore",
    "ChromaVectorStore",
    "Retriever",
    "KnowledgeSource",
    "HackTricksSource",
    "HackTricksRetriever",
    # Storage
    "ChromaDBStore",
    "MetadataStorage",
    # Config
    "KnowledgeConfig",
    # Exceptions
    "WishKnowledgeError",
    "KnowledgeSourceError",
    "ExtractionError",
    "StorageError",
    "EmbeddingError",
]

__version__ = "0.1.0"
