"""Command-line interface for wish-knowledge-loader."""

import logging

import click
from wish_models.knowledge.knowledge_metadata import KnowledgeMetadata, KnowledgeMetadataContainer
from wish_models.utc_datetime import UtcDatetime

from wish_knowledge_loader.nodes.document_loader import DocumentLoader
from wish_knowledge_loader.nodes.repo_cloner import RepoCloner
from wish_knowledge_loader.nodes.vector_store import VectorStore
from wish_knowledge_loader.settings import Settings
from wish_knowledge_loader.utils.logging_utils import setup_logger


@click.command()
@click.option("--repo-url", required=True, help="GitHub repository URL")
@click.option("--glob", required=True, help="Glob pattern for files to include")
@click.option("--title", required=True, help="Knowledge base title")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.option("--debug", "-d", is_flag=True, help="Enable debug logging (even more verbose)")
def main(repo_url: str, glob: str, title: str, verbose: bool = False, debug: bool = False) -> int:
    """CLI tool for cloning GitHub repositories and storing them in a vector database."""
    try:
        # Set up logging
        log_level = logging.DEBUG if debug else (logging.INFO if verbose else logging.WARNING)
        logger = setup_logger("wish-knowledge-loader", level=log_level)
        logger.info(f"Starting knowledge loader with log level: {logging.getLevelName(log_level)}")

        # Load settings
        logger.info("Loading settings")
        settings = Settings()
        logger.debug(f"WISH_HOME: {settings.WISH_HOME}")
        logger.debug(f"Knowledge directory: {settings.knowledge_dir}")
        logger.debug(f"Repository directory: {settings.repo_dir}")
        logger.debug(f"Database directory: {settings.db_dir}")
        logger.debug(f"Metadata path: {settings.meta_path}")

        # Load metadata container
        logger.info("Loading metadata container")
        container = KnowledgeMetadataContainer.load(settings.meta_path)
        logger.debug(f"Loaded metadata container with {len(container.m)} entries")

        # Clone repository
        logger.info(f"Cloning repository: {repo_url}")
        repo_cloner = RepoCloner(settings, logger=logger)
        repo_path = repo_cloner.clone(repo_url)
        logger.info(f"Repository cloned to: {repo_path}")

        # Load documents
        logger.info(f"Loading documents with pattern: {glob}")
        document_loader = DocumentLoader(settings, logger=logger)
        documents = document_loader.load(repo_path, glob)
        logger.info(f"Loaded {len(documents)} documents")

        # Split documents
        chunk_size = 1000
        chunk_overlap = 100
        logger.info(f"Splitting documents (chunk_size={chunk_size}, chunk_overlap={chunk_overlap})")
        split_docs = document_loader.split(documents, chunk_size, chunk_overlap)
        logger.info(f"Split into {len(split_docs)} chunks")

        # Store in vector store
        logger.info(f"Storing documents in vector store: {title}")
        vector_store = VectorStore(settings, logger=logger)
        vector_store.store(title, split_docs)
        logger.info("Documents stored in vector store")

        # Create metadata
        logger.info(f"Creating metadata for knowledge base: {title}")
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
        logger.debug(f"Created metadata: {metadata.title}")

        # Add metadata
        logger.info("Adding metadata to container")
        container.add(metadata)
        logger.debug(f"Container now has {len(container.m)} entries")

        # Save metadata
        logger.info(f"Saving metadata to {settings.meta_path}")
        container.save(settings.meta_path)
        logger.info("Metadata saved successfully")

        logger.info(f"Knowledge base loaded successfully: {title}")
        click.echo(f"Successfully loaded knowledge base: {title}")
        return 0
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        click.echo(f"Error: {str(e)}", err=True)
        return 1


if __name__ == "__main__":
    main()  # pragma: no cover
