"""Vector store implementation using ChromaDB."""

import logging
from typing import Any

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from openai import OpenAI

from .config import EmbeddingConfig, KnowledgeConfig
from .exceptions import EmbeddingError, StorageError

logger = logging.getLogger(__name__)


class ChromaDBStore:
    """ChromaDB vector store for HackTricks knowledge."""

    def __init__(self, config: KnowledgeConfig) -> None:
        """Initialize ChromaDB store."""
        self.config = config
        self.embedding_config = config.embedding

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(config.get_chromadb_path()),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )

        # Initialize embedding function
        self.embedding_function = self._create_embedding_function()

        # Collection will be created/loaded on demand
        self._collection: Any | None = None

    def _create_embedding_function(self) -> Any:
        """Create embedding function based on configuration."""
        if self.embedding_config.provider == "openai":
            if not self.embedding_config.api_key:
                raise EmbeddingError("OpenAI API key not provided")

            return embedding_functions.OpenAIEmbeddingFunction(
                api_key=self.embedding_config.api_key,
                model_name=self.embedding_config.model,
            )
        elif self.embedding_config.provider == "local":
            # Use sentence-transformers for local embeddings
            return embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        else:
            raise EmbeddingError(f"Unknown embedding provider: {self.embedding_config.provider}")

    @property
    def collection(self) -> Any:
        """Get or create the collection."""
        if self._collection is None:
            self._collection = self._get_or_create_collection()
        return self._collection

    def _get_or_create_collection(self) -> Any:
        """Get existing collection or create new one."""
        collection_name = "hacktricks_knowledge"

        try:
            # Try to get existing collection
            return self.client.get_collection(
                name=collection_name,
                embedding_function=self.embedding_function,
            )
        except Exception:
            # Create new collection
            logger.info(f"Creating new collection: {collection_name}")
            return self.client.create_collection(
                name=collection_name,
                embedding_function=self.embedding_function,
                metadata={"description": "HackTricks penetration testing knowledge base"},
            )

    def add_documents(
        self,
        documents: list[str],
        metadatas: list[dict[str, Any]],
        ids: list[str],
    ) -> None:
        """Add documents to the vector store."""
        try:
            # Process in batches
            batch_size = self.embedding_config.batch_size
            # OpenAI embedding model has a max context length of 8192 tokens
            # Technical content tends to have more tokens per character
            # Using conservative estimate of ~2.5 chars per token, limit to 20000 chars
            max_chunk_length = 20000

            for i in range(0, len(documents), batch_size):
                batch_end = min(i + batch_size, len(documents))

                batch_docs = []
                batch_metas = []
                batch_ids = []

                for j in range(i, batch_end):
                    doc = documents[j]
                    doc_id = ids[j]
                    doc_meta = metadatas[j]

                    # Check if document is too long
                    if len(doc) > max_chunk_length:
                        logger.warning(f"Document too long ({len(doc)} chars), splitting into parts")

                        # Split document into smaller parts
                        parts = self._split_long_document(doc, max_chunk_length)

                        # Add each part with updated metadata and ID
                        for part_idx, part in enumerate(parts):
                            part_meta = doc_meta.copy()
                            part_meta["part_number"] = part_idx + 1
                            part_meta["total_parts"] = len(parts)

                            batch_docs.append(part)
                            batch_metas.append(part_meta)
                            batch_ids.append(f"{doc_id}_part_{part_idx + 1}")
                    else:
                        batch_docs.append(doc)
                        batch_metas.append(doc_meta)
                        batch_ids.append(doc_id)

                # Try to add batch, but continue if individual documents fail
                if batch_docs:
                    try:
                        self.collection.add(
                            documents=batch_docs,
                            metadatas=batch_metas,
                            ids=batch_ids,
                        )
                    except Exception as batch_error:
                        # If batch fails, try adding documents individually
                        logger.warning(f"Batch add failed, trying individual documents: {batch_error}")
                        for k in range(len(batch_docs)):
                            try:
                                self.collection.add(
                                    documents=[batch_docs[k]],
                                    metadatas=[batch_metas[k]],
                                    ids=[batch_ids[k]],
                                )
                            except Exception as doc_error:
                                logger.error(f"Failed to add document {batch_ids[k]}: {doc_error}")
                                # Continue with next document

                # Progress callback
                if self.config.progress_callback:
                    progress = min((i + len(batch_docs)) / len(documents) * 100, 100)
                    self.config.progress_callback("embedding", progress)

                logger.debug(f"Added batch {i // batch_size + 1}, total documents: {i + len(batch_docs)}")

        except Exception as e:
            raise StorageError(f"Failed to add documents: {e}") from e

    def _split_long_document(self, text: str, max_length: int) -> list[str]:
        """Split a long document into smaller parts at sentence boundaries."""
        import re

        # Try to split at paragraph boundaries first
        paragraphs = text.split("\n\n")

        parts = []
        current_part = ""

        for para in paragraphs:
            # If adding this paragraph would exceed limit
            if len(current_part) + len(para) + 2 > max_length:
                if current_part:
                    parts.append(current_part.strip())
                    current_part = ""

                # If paragraph itself is too long, split by sentences
                if len(para) > max_length:
                    # Split by sentences (simple approach)
                    sentences = re.split(r"(?<=[.!?])\s+", para)

                    for sentence in sentences:
                        if len(current_part) + len(sentence) + 1 > max_length:
                            if current_part:
                                parts.append(current_part.strip())
                                current_part = ""

                            # If sentence is still too long, hard split
                            if len(sentence) > max_length:
                                # Split sentence into chunks
                                chunk_size = int(max_length - 100)  # Leave some margin
                                for k in range(0, len(sentence), chunk_size):
                                    parts.append(sentence[k : k + chunk_size])
                            else:
                                current_part = sentence
                        else:
                            current_part += " " + sentence if current_part else sentence
                else:
                    current_part = para
            else:
                current_part += "\n\n" + para if current_part else para

        # Add any remaining content
        if current_part:
            parts.append(current_part.strip())

        return parts

    def search(
        self,
        query: str,
        n_results: int = 5,
        where: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Search for relevant documents."""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where,
            )

            # Format results
            formatted_results = []
            if results["documents"] and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    formatted_results.append(
                        {
                            "content": doc,
                            "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                            "distance": results["distances"][0][i] if results["distances"] else 0.0,
                            "id": results["ids"][0][i] if results["ids"] else "",
                        }
                    )

            return {
                "query": query,
                "results": formatted_results,
                "total": len(formatted_results),
            }

        except Exception as e:
            raise StorageError(f"Search failed: {e}") from e

    def update_metadata(self, ids: list[str], metadatas: list[dict[str, Any]]) -> None:
        """Update metadata for existing documents."""
        try:
            self.collection.update(
                ids=ids,
                metadatas=metadatas,
            )
        except Exception as e:
            raise StorageError(f"Failed to update metadata: {e}") from e

    def delete(self, ids: list[str]) -> None:
        """Delete documents by IDs."""
        try:
            self.collection.delete(ids=ids)
        except Exception as e:
            raise StorageError(f"Failed to delete documents: {e}") from e

    def get_stats(self) -> dict[str, Any]:
        """Get collection statistics."""
        try:
            count = self.collection.count()
            return {
                "total_documents": count,
                "collection_name": self.collection.name,
                "embedding_model": self.embedding_config.model,
            }
        except Exception as e:
            raise StorageError(f"Failed to get stats: {e}") from e

    def reset(self) -> None:
        """Reset the entire collection."""
        try:
            self.client.delete_collection("hacktricks_knowledge")
            self._collection = None
            logger.info("Collection reset completed")
        except Exception as e:
            raise StorageError(f"Failed to reset collection: {e}") from e


class EmbeddingService:
    """Service for generating embeddings directly."""

    def __init__(self, config: EmbeddingConfig) -> None:
        """Initialize embedding service."""
        self.config = config

        if config.provider == "openai":
            if not config.api_key:
                raise EmbeddingError("OpenAI API key not provided")
            self.client = OpenAI(api_key=config.api_key)
        else:
            # For local embeddings, we'll use the ChromaDB embedding function
            self.embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )

    def embed_text(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        try:
            if self.config.provider == "openai":
                response = self.client.embeddings.create(
                    model=self.config.model,
                    input=text,
                )
                return response.data[0].embedding
            else:
                # Local embedding
                embeddings = self.embedding_func([text])
                return embeddings[0]
        except Exception as e:
            raise EmbeddingError(f"Failed to generate embedding: {e}") from e

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        try:
            if self.config.provider == "openai":
                response = self.client.embeddings.create(
                    model=self.config.model,
                    input=texts,
                )
                return [item.embedding for item in response.data]
            else:
                # Local embeddings
                return self.embedding_func(texts)
        except Exception as e:
            raise EmbeddingError(f"Failed to generate embeddings: {e}") from e
