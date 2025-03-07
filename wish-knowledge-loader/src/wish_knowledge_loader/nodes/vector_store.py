"""Vector store functionality."""

from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document
from langchain_community.vectorstores import Chroma

from wish_knowledge_loader.settings import Settings


class VectorStore:
    """Class for managing vector stores."""

    def __init__(self, settings: Settings):
        """Initialize the VectorStore.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.embeddings = OpenAIEmbeddings(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
            disallowed_special=()  # Disable special token checking
        )

    def store(self, title: str, documents: list[Document]) -> None:
        """Store documents in a vector store.

        Args:
            title: Knowledge base title
            documents: List of documents
        """
        # Create path for vector store
        db_path = self.settings.db_dir / title

        # Create vector store using Chroma
        # Note: Since Chroma 0.4.x, documents are automatically persisted
        Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            persist_directory=str(db_path)
        )
