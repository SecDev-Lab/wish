"""Command-line interface for wish-knowledge-loader."""

import click

from wish_knowledge_loader.models.knowledge_metadata import KnowledgeMetadata, KnowledgeMetadataContainer
from wish_knowledge_loader.nodes.document_loader import DocumentLoader
from wish_knowledge_loader.nodes.repo_cloner import RepoCloner
from wish_knowledge_loader.nodes.vector_store import VectorStore
from wish_knowledge_loader.settings import Settings
from wish_models.utc_datetime import UtcDatetime


@click.command()
@click.option("--repo-url", required=True, help="GitHub repository URL")
@click.option("--glob", required=True, help="Glob pattern for files to include")
@click.option("--title", required=True, help="Knowledge base title")
def main(repo_url: str, glob: str, title: str) -> int:
    """CLI tool for cloning GitHub repositories and storing them in a vector database."""
    try:
        # Load settings
        settings = Settings()

        # Load metadata container
        container = KnowledgeMetadataContainer.load(settings.meta_path)

        # Clone repository
        repo_cloner = RepoCloner(settings)
        repo_path = repo_cloner.clone(repo_url)

        # Load documents
        document_loader = DocumentLoader(settings)
        documents = document_loader.load(repo_path, glob)

        # Split documents
        chunk_size = 1000
        chunk_overlap = 100
        split_docs = document_loader.split(documents, chunk_size, chunk_overlap)

        # Store in vector store
        vector_store = VectorStore(settings)
        vector_store.store(title, split_docs)

        # Create metadata
        metadata = KnowledgeMetadata(
            title=title,
            repo_url=repo_url,
            glob_pattern=glob,
            repo_path=repo_path,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            created_at=UtcDatetime.now(),
            updated_at=UtcDatetime.now()
        )

        # Add metadata
        container.add(metadata)

        # Save metadata
        container.save(settings.meta_path)

        click.echo(f"Successfully loaded knowledge base: {title}")
        return 0
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        return 1


if __name__ == "__main__":
    main()  # pragma: no cover
