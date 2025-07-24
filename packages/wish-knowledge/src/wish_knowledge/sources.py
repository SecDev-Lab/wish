"""Knowledge sources implementation."""

import logging
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import aiofiles
import git

from .config import KnowledgeConfig
from .exceptions import KnowledgeSourceError
from .splitter import DocumentChunk, HackTricksMarkdownSplitter
from .storage import CacheStorage, MetadataStorage
from .vectorstore import ChromaDBStore

logger = logging.getLogger(__name__)


class KnowledgeSource(ABC):
    """Abstract knowledge source interface."""

    @abstractmethod
    async def fetch_content(self) -> list[dict[str, Any]]:
        """Fetch content from the knowledge source."""
        pass

    @abstractmethod
    async def process_and_store(self) -> dict[str, Any]:
        """Process content and store in knowledge base."""
        pass


class HackTricksSource(KnowledgeSource):
    """HackTricks knowledge source implementation."""

    def __init__(self, config: KnowledgeConfig) -> None:
        """Initialize HackTricks source."""
        self.config = config
        self.hacktricks_config = config.hacktricks

        # Initialize components
        self.splitter = HackTricksMarkdownSplitter(
            chunk_size=self.hacktricks_config.chunk_size,
            chunk_overlap=self.hacktricks_config.chunk_overlap,
        )
        self.vectorstore = ChromaDBStore(config)
        self.metadata_storage = MetadataStorage(config)
        self.cache_storage = CacheStorage(config)

    async def fetch_content(self) -> list[dict[str, Any]]:
        """Fetch HackTricks content from GitHub."""
        logger.info("Fetching HackTricks content...")

        # Create temporary directory for cloning
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Clone repository
                logger.info(f"Cloning HackTricks repository to {temp_dir}")
                git.Repo.clone_from(
                    self.hacktricks_config.repo_url,
                    temp_dir,
                    depth=self.hacktricks_config.clone_depth,
                )

                # Process markdown files
                documents = await self._process_markdown_files(Path(temp_dir))

                logger.info(f"Fetched {len(documents)} documents from HackTricks")
                return documents

            except Exception as e:
                raise KnowledgeSourceError(f"Failed to fetch HackTricks content: {e}") from e

    async def _process_markdown_files(self, repo_path: Path) -> list[dict[str, Any]]:
        """Process all markdown files in the repository."""
        documents = []
        markdown_files = list(repo_path.rglob("*.md"))

        # Progress tracking
        total_files = len(markdown_files)
        processed = 0

        for md_file in markdown_files:
            try:
                # Skip certain files
                if any(skip in str(md_file) for skip in [".git", "node_modules", "README"]):
                    continue

                # Read file content
                async with aiofiles.open(md_file, encoding="utf-8") as f:
                    content = await f.read()

                # Extract metadata
                relative_path = md_file.relative_to(repo_path)
                category = self._extract_category(relative_path)

                # Create document
                doc = {
                    "content": content,
                    "metadata": {
                        "source": str(relative_path),
                        "category": category,
                        "url": f"https://book.hacktricks.xyz/{relative_path.with_suffix('')}",
                        "has_code": "```" in content,
                        "has_tables": "|" in content and "---" in content,
                    },
                }

                documents.append(doc)

                # Cache the content
                await self._cache_document(doc)

                # Update progress
                processed += 1
                if self.config.progress_callback:
                    progress = (processed / total_files) * 100
                    self.config.progress_callback("fetching", progress)

            except Exception as e:
                logger.warning(f"Failed to process {md_file}: {e}")
                continue

        return documents

    def _extract_category(self, path: Path) -> str:
        """Extract category from file path."""
        parts = path.parts

        # Common categories in HackTricks
        category_keywords = {
            "pentesting": "methodology",
            "web": "web_exploitation",
            "windows": "windows",
            "linux": "linux",
            "network": "network",
            "mobile": "mobile",
            "cloud": "cloud",
            "crypto": "cryptography",
            "forensics": "forensics",
        }

        for part in parts:
            part_lower = part.lower()
            for keyword, category in category_keywords.items():
                if keyword in part_lower:
                    return category

        return "general"

    async def _cache_document(self, doc: dict[str, Any]) -> None:
        """Cache document for offline use."""
        url = doc["metadata"].get("url", "")
        if url:
            self.cache_storage.save_page(url, doc["content"])

    async def process_and_store(self) -> dict[str, Any]:
        """Process HackTricks content and store in knowledge base."""
        logger.info("Processing and storing HackTricks knowledge...")

        # Check if update is needed
        if not self.metadata_storage.should_update():
            logger.info("Knowledge base is up to date")
            return {"status": "up_to_date", "processed": 0}

        # Progress: Fetching (0-30%)
        if self.config.progress_callback:
            self.config.progress_callback("fetching", 0)

        # Fetch content
        documents = await self.fetch_content()

        if not documents:
            return {"status": "no_content", "processed": 0}

        if self.config.progress_callback:
            self.config.progress_callback("fetching", 30)

        # Progress: Processing (30-70%)
        all_chunks: list[DocumentChunk] = []

        for i, doc in enumerate(documents):
            # Split into chunks
            chunks = self._create_chunks(doc)
            all_chunks.extend(chunks)

            # Progress update
            if self.config.progress_callback:
                progress = 30 + ((i + 1) / len(documents)) * 40  # 30-70%
                self.config.progress_callback("processing", progress)

        # Progress: Storing (70-100%)
        if self.config.progress_callback:
            self.config.progress_callback("storing", 70)

        # Store in vector database
        await self._store_in_vectordb(all_chunks)

        if self.config.progress_callback:
            self.config.progress_callback("storing", 95)

        # Update metadata
        metadata = {
            "total_documents": len(documents),
            "total_chunks": len(all_chunks),
            "source": "hacktricks",
            "version": "1.0",
        }
        self.metadata_storage.save_metadata(metadata)

        if self.config.progress_callback:
            self.config.progress_callback("complete", 100)

        logger.info(f"Stored {len(all_chunks)} chunks")

        return {
            "status": "success",
            "processed": len(documents),
            "chunks": len(all_chunks),
        }

    def _create_chunks(self, doc: dict[str, Any]) -> list[DocumentChunk]:
        """Create chunks from a document."""
        chunks = []

        # Split content
        text_chunks = self.splitter.split_text(doc["content"])

        for i, chunk_text in enumerate(text_chunks):
            chunk = DocumentChunk(
                text=chunk_text,
                metadata={
                    **doc["metadata"],
                    "chunk_id": i,
                    "total_chunks": len(text_chunks),
                },
                chunk_id=i,
                total_chunks=len(text_chunks),
            )
            chunks.append(chunk)

        return chunks

    async def _store_in_vectordb(self, chunks: list[DocumentChunk]) -> None:
        """Store chunks in vector database."""
        logger.info(f"Storing {len(chunks)} chunks in vector database...")

        # Prepare data for ChromaDB
        documents = []
        metadatas = []
        ids = []

        for i, chunk in enumerate(chunks):
            documents.append(chunk.text)
            metadatas.append(chunk.metadata)
            ids.append(f"chunk_{i}")

        # Store in batches
        self.vectorstore.add_documents(documents, metadatas, ids)


class HackTricksRetriever:
    """Retriever for HackTricks knowledge."""

    def __init__(self, config: KnowledgeConfig) -> None:
        """Initialize retriever."""
        self.config = config
        self.vectorstore = ChromaDBStore(config)

    async def search(
        self,
        query: str,
        limit: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Search for relevant knowledge."""
        results = self.vectorstore.search(query, n_results=limit, where=filters)
        return results.get("results", [])
