#!/usr/bin/env python
"""Script to search documents from a persistent vector store."""

import os
import sys
from collections import defaultdict
from pathlib import Path

from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings


def load_full_document(file_path):
    """Load the full content of a document.
    
    Args:
        file_path: Path to the document file
        
    Returns:
        The full content of the document as a string
    """
    try:
        loader = TextLoader(file_path)
        documents = loader.load()
        if documents:
            return documents[0].page_content
        return None
    except Exception as e:
        print(f"Error loading document {file_path}: {str(e)}")
        return None


def main():
    """Search documents from a persistent vector store."""
    # Check if knowledge title is provided
    if len(sys.argv) < 2:
        print("Usage: python search_knowledge.py <knowledge_title> <query>")
        sys.exit(1)

    # Get knowledge title and query from command line arguments
    knowledge_title = sys.argv[1]
    query = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "test"

    # Check if OpenAI API key is set
    if "OPENAI_API_KEY" not in os.environ:
        print("Error: OPENAI_API_KEY environment variable is not set")
        sys.exit(1)

    # Get embedding model from environment variable or use default
    embedding_model = os.environ.get("OPENAI_MODEL", "text-embedding-3-small")

    # Get knowledge base path
    wish_home = Path(os.environ.get("WISH_HOME", os.path.expanduser("~/.wish")))
    db_path = wish_home / "knowledge" / "db" / knowledge_title
    repo_path = wish_home / "knowledge" / "repo" / knowledge_title.split('/')[-1]

    # Check if knowledge base exists
    if not db_path.exists():
        print(f"Error: Knowledge base '{knowledge_title}' not found at {db_path}")
        sys.exit(1)

    # Initialize embedding model
    embeddings = OpenAIEmbeddings(
        model=embedding_model,
        disallowed_special=()
    )

    # Load vector store
    print(f"Loading vector store: {knowledge_title}")
    vectorstore = Chroma(
        persist_directory=str(db_path),
        embedding_function=embeddings
    )

    # Search for similar documents
    print(f"Searching for: {query}")
    chunks = vectorstore.similarity_search(query, k=4)

    # Group chunks by source document
    documents_dict = defaultdict(list)
    for chunk in chunks:
        source = chunk.metadata.get('source')
        if source:
            documents_dict[source].append(chunk)

    # Display results
    print(f"Found chunks from {len(documents_dict)} documents")

    for i, (source, chunks) in enumerate(documents_dict.items()):
        print(f"\nDocument {i+1}: {source}")

        # Try to load the full document
        full_path = None
        if source.startswith('/'):
            # Absolute path
            full_path = source
        else:
            # Relative path - try to find in repo directory
            full_path = repo_path / source
            if not full_path.exists():
                # Try alternative paths
                alt_path = Path(source)
                if alt_path.exists():
                    full_path = alt_path

        if full_path and Path(full_path).exists():
            full_content = load_full_document(str(full_path))
            if full_content:
                print("Full document content:")
                print("-" * 50)
                print(full_content)
                print("-" * 50)
            else:
                print("Could not load full document content. Showing chunks instead:")
                for j, chunk in enumerate(chunks):
                    print(f"\nChunk {j+1}:")
                    print(f"Content: {chunk.page_content}")
                    print("-" * 30)
        else:
            print("Source file not found. Showing chunks instead:")
            for j, chunk in enumerate(chunks):
                print(f"\nChunk {j+1}:")
                print(f"Content: {chunk.page_content}")
                print("-" * 30)

        # Show metadata from first chunk
        if chunks:
            print(f"Metadata: {chunks[0].metadata}")

        print("=" * 70)


if __name__ == "__main__":
    main()
