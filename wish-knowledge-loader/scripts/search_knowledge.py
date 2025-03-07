#!/usr/bin/env python
"""Script to search documents from a persistent vector store."""

import os
import sys
from pathlib import Path

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma


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
    documents = vectorstore.similarity_search(query, k=4)

    # Display results
    print(f"Found {len(documents)} documents")
    for i, doc in enumerate(documents):
        print(f"\nResult {i+1}:")
        print(f"Content: {doc.page_content[:100]}...")
        print(f"Metadata: {doc.metadata}")
        print("-" * 50)


if __name__ == "__main__":
    main()
