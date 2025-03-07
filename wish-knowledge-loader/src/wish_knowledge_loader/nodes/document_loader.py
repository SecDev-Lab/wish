"""Document loading functionality."""

from pathlib import Path

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

from wish_knowledge_loader.settings import Settings


class DocumentLoader:
    """Class for loading documents."""

    def __init__(self, settings: Settings):
        """Initialize the DocumentLoader.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.TextLoader = TextLoader  # For easier mocking in tests

    def load(self, repo_path: Path, glob_pattern: str) -> list[Document]:
        """Load files matching the specified pattern.

        Args:
            repo_path: Path to the repository
            glob_pattern: Glob pattern

        Returns:
            List of loaded documents
        """
        # Use DirectoryLoader to load files
        loader = DirectoryLoader(
            str(repo_path),
            glob=glob_pattern,
            loader_cls=self.TextLoader
        )
        documents = loader.load()

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
        # Use RecursiveCharacterTextSplitter to split documents
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        split_docs = text_splitter.split_documents(documents)

        return split_docs
