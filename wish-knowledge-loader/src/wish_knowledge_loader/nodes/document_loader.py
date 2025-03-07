"""Document loading functionality."""

import logging
from pathlib import Path

from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, TextLoader

from wish_knowledge_loader.settings import Settings
from wish_knowledge_loader.utils.logging_utils import setup_logger


class DocumentLoader:
    """Class for loading documents."""

    def __init__(self, settings: Settings, logger: logging.Logger = None):
        """Initialize the DocumentLoader.

        Args:
            settings: Application settings
            logger: Logger instance
        """
        self.settings = settings
        self.TextLoader = TextLoader  # For easier mocking in tests
        self.logger = logger or setup_logger("wish-knowledge-loader.document_loader")

    def load(self, repo_path: Path, glob_pattern: str) -> list[Document]:
        """Load files matching the specified pattern.

        Args:
            repo_path: Path to the repository
            glob_pattern: Glob pattern

        Returns:
            List of loaded documents
        """
        self.logger.info(f"Loading documents from {repo_path} with pattern: {glob_pattern}")

        # Use DirectoryLoader to load files
        loader = DirectoryLoader(
            str(repo_path),
            glob=glob_pattern,
            loader_cls=self.TextLoader
        )

        self.logger.debug(f"Created DirectoryLoader with glob pattern: {glob_pattern}")
        self.logger.info("Loading documents...")
        documents = loader.load()
        self.logger.info(f"Loaded {len(documents)} documents")

        # Log some information about the documents
        if documents:
            self.logger.debug(f"First document source: {documents[0].metadata.get('source', 'unknown')}")
            self.logger.debug(f"First document length: {len(documents[0].page_content)} characters")

        return documents

    def split(self, documents: list[Document], chunk_size: int, chunk_overlap: int) -> list[Document]:
        """Split documents into chunks.

        Args:
            documents: List of documents
            chunk_size: Chunk size
            chunk_overlap: Chunk overlap

        Returns:
            List of split documents
        """
        self.logger.info(
            f"Splitting {len(documents)} documents into chunks (size={chunk_size}, overlap={chunk_overlap})"
        )

        # Use RecursiveCharacterTextSplitter to split documents
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

        self.logger.debug("Created RecursiveCharacterTextSplitter")
        self.logger.info("Splitting documents...")
        split_docs = text_splitter.split_documents(documents)
        self.logger.info(f"Split into {len(split_docs)} chunks")

        # Log some information about the chunks
        if split_docs:
            avg_chunk_size = sum(len(doc.page_content) for doc in split_docs) / len(split_docs)
            self.logger.debug(f"Average chunk size: {avg_chunk_size:.2f} characters")

        return split_docs
