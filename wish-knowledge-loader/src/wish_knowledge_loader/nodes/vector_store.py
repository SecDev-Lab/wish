"""Vector store functionality."""

import logging

from langchain.schema import Document
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

from wish_knowledge_loader.settings import Settings
from wish_knowledge_loader.utils.logging_utils import setup_logger


class VectorStore:
    """Class for managing vector stores."""

    def __init__(self, settings: Settings, logger: logging.Logger = None):
        """Initialize the VectorStore.

        Args:
            settings: Application settings
            logger: Logger instance
        """
        self.settings = settings
        self.logger = logger or setup_logger("wish-knowledge-loader.vector_store")

        self.logger.debug(f"Initializing OpenAI embeddings with model: {settings.OPENAI_MODEL}")
        self.embeddings = OpenAIEmbeddings(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
            disallowed_special=()  # Disable special token checking
        )
        self.logger.debug("OpenAI embeddings initialized")

    def store(self, title: str, documents: list[Document]) -> None:
        """Store documents in a vector store.

        Args:
            title: Knowledge base title
            documents: List of documents
        """
        self.logger.info(f"Storing {len(documents)} documents in vector store: {title}")

        # Create path for vector store
        db_path = self.settings.db_dir / title
        self.logger.debug(f"Vector store path: {db_path}")

        # Create vector store using Chroma
        self.logger.info("Creating Chroma vector store...")
        # Note: Since Chroma 0.4.x, documents are automatically persisted
        self.logger.debug(f"Using embedding model: {self.settings.OPENAI_MODEL}")

        # This operation can take a long time for large document collections
        self.logger.info("Starting vector embedding process (this may take a while)...")
        vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            persist_directory=str(db_path)
        )
        self.logger.info(f"Successfully stored {len(documents)} documents in vector store")
        self.logger.debug(f"Vector store contains {vectorstore._collection.count()} vectors")
