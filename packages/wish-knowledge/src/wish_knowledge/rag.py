"""RAG implementation for wish-knowledge."""

from abc import ABC, abstractmethod
from typing import Any

from .config import KnowledgeConfig
from .sources import HackTricksRetriever
from .vectorstore import ChromaDBStore


class VectorStore(ABC):
    """Abstract vector store interface."""

    @abstractmethod
    async def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        """Search for relevant documents."""
        pass


class ChromaVectorStore(VectorStore):
    """ChromaDB implementation of vector store."""

    def __init__(self, config: KnowledgeConfig) -> None:
        """Initialize ChromaDB vector store."""
        self.store = ChromaDBStore(config)

    async def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        """Search for relevant documents."""
        results = self.store.search(query, n_results=limit)
        return results.get("results", [])


class Retriever:
    """Document retriever for RAG."""

    def __init__(self, vector_store: VectorStore | None = None, config: KnowledgeConfig | None = None) -> None:
        """Initialize retriever with vector store or config."""
        if vector_store:
            self.vector_store = vector_store
            self.hacktricks_retriever = None
        elif config:
            self.vector_store = ChromaVectorStore(config)
            self.hacktricks_retriever = HackTricksRetriever(config)
        else:
            raise ValueError("Either vector_store or config must be provided")

    async def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        """Search for relevant documents."""
        return await self.vector_store.search(query, limit=limit)

    async def retrieve(self, query: str) -> list[str]:
        """Retrieve relevant documents."""
        results = await self.vector_store.search(query)
        return [doc.get("content", "") for doc in results]

    async def search_with_context(
        self,
        query: str,
        limit: int = 5,
        category: str | None = None,
        has_code: bool | None = None,
    ) -> list[dict[str, Any]]:
        """Search with additional context filters."""
        filters = {}

        if category:
            filters["category"] = category

        if has_code is not None:
            filters["has_code"] = has_code

        if self.hacktricks_retriever:
            return await self.hacktricks_retriever.search(query, limit=limit, filters=filters if filters else None)

        # Fallback to basic search
        return await self.search(query, limit)
