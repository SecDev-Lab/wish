"""Command-line interface for wish-knowledge-loader."""

import logging
import shutil

import click
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from wish_models.knowledge.knowledge_metadata import KnowledgeMetadata, KnowledgeMetadataContainer
from wish_models.settings import Settings, get_default_env_path
from wish_models.utc_datetime import UtcDatetime

from wish_knowledge_loader.nodes.document_loader import DocumentLoader
from wish_knowledge_loader.nodes.repo_cloner import RepoCloner
from wish_knowledge_loader.nodes.vector_store import VectorStore
from wish_knowledge_loader.utils.logging_utils import setup_logger


@click.group()
def main():
    """CLI tool for managing knowledge bases."""
    pass


@main.command("load")
@click.option("--repo-url", required=True, help="GitHub repository URL")
@click.option("--glob", required=True, help="Glob pattern for files to include")
@click.option("--title", required=True, help="Knowledge base title")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.option("--debug", "-d", is_flag=True, help="Enable debug logging (even more verbose)")
def load_knowledge(repo_url: str, glob: str, title: str, verbose: bool = False, debug: bool = False) -> int:
    """Load a knowledge base from a GitHub repository."""
    try:
        # Set up logging
        log_level = logging.DEBUG if debug else (logging.INFO if verbose else logging.WARNING)
        logger = setup_logger("wish-knowledge-loader", level=log_level)
        logger.info(f"Starting knowledge loader with log level: {logging.getLevelName(log_level)}")

        # Create settings instance
        env_path = get_default_env_path()
        settings = Settings(env_file=env_path)

        # Log settings
        logger.info("Loading settings")
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
        repo_cloner = RepoCloner(settings_obj=settings, logger=logger)
        repo_path = repo_cloner.clone(repo_url)
        logger.info(f"Repository cloned to: {repo_path}")

        # Load documents
        logger.info(f"Loading documents with pattern: {glob}")
        document_loader = DocumentLoader(settings_obj=settings, logger=logger)
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
        vector_store = VectorStore(settings_obj=settings, logger=logger)
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


@main.command("list")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.option("--debug", "-d", is_flag=True, help="Enable debug logging")
def list_knowledge(verbose: bool = False, debug: bool = False) -> int:
    """List all loaded knowledge bases."""
    try:
        # Set up logging
        log_level = logging.DEBUG if debug else (logging.INFO if verbose else logging.WARNING)
        logger = setup_logger("wish-knowledge-loader", level=log_level)

        # Create settings instance
        env_path = get_default_env_path()
        settings = Settings(env_file=env_path)

        # Load metadata container
        container = KnowledgeMetadataContainer.load(settings.meta_path)

        if not container.m:
            click.echo("No knowledge bases found.")
            return 0

        # Display information for each knowledge base
        click.echo(f"Found {len(container.m)} knowledge bases:")
        for title, metadata in container.m.items():
            click.echo(f"\n- Title: {title}")
            click.echo(f"  Repository: {metadata.repo_url}")
            click.echo(f"  Pattern: {metadata.glob_pattern}")
            click.echo(f"  Created: {metadata.created_at}")
            click.echo(f"  Updated: {metadata.updated_at}")

        return 0
    except Exception as e:
        logger = logging.getLogger("wish-knowledge-loader")
        logger.error(f"Error: {str(e)}", exc_info=True)
        click.echo(f"Error: {str(e)}", err=True)
        return 1


@main.command("delete")
@click.option("--title", required=True, help="Knowledge base title to delete")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation prompt")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.option("--debug", "-d", is_flag=True, help="Enable debug logging")
def delete_knowledge(title: str, force: bool = False, verbose: bool = False, debug: bool = False) -> int:
    """Delete a knowledge base."""
    try:
        # Set up logging
        log_level = logging.DEBUG if debug else (logging.INFO if verbose else logging.WARNING)
        logger = setup_logger("wish-knowledge-loader", level=log_level)

        # Create settings instance
        env_path = get_default_env_path()
        settings = Settings(env_file=env_path)

        # Load metadata container
        container = KnowledgeMetadataContainer.load(settings.meta_path)

        # Check if the specified knowledge base exists
        metadata = container.get(title)
        if not metadata:
            click.echo(f"Knowledge base '{title}' not found.", err=True)
            return 1

        # Check for dependencies - find other knowledge bases using the same repository
        dependent_knowledge = []
        for other_title, other_metadata in container.m.items():
            if other_title != title and other_metadata.repo_url == metadata.repo_url:
                dependent_knowledge.append(other_title)

        # Confirmation prompt
        if not force:
            message = f"Are you sure you want to delete knowledge base '{title}'?"

            if not click.confirm(message):
                click.echo("Operation cancelled.")
                return 0

        # Delete vector database directory
        db_path = settings.db_dir / title
        if db_path.exists():
            # Use Chroma API for proper deletion
            logger.info(f"Deleting vector database at {db_path}")

            embeddings = OpenAIEmbeddings(
                api_key=settings.OPENAI_API_KEY,
                model=settings.OPENAI_EMBEDDING_MODEL,
                disallowed_special=()
            )

            # Delete using Chroma API
            try:
                vectorstore = Chroma(
                    persist_directory=str(db_path),
                    embedding_function=embeddings
                )
                vectorstore.delete_collection()
                logger.info("Vector database deleted via Chroma API")
            except Exception as e:
                logger.warning(f"Failed to delete via Chroma API: {e}")

            # Remove directory
            shutil.rmtree(db_path, ignore_errors=True)
            logger.info("Vector database directory removed")

        # Delete repository directory only if this is the last knowledge base using it
        if not dependent_knowledge:
            repo_path = metadata.repo_path
            if repo_path.exists():
                logger.info(f"Deleting repository at {repo_path} (last knowledge base using this repository)")
                shutil.rmtree(repo_path, ignore_errors=True)
                logger.info("Repository directory removed")
        else:
            logger.info(f"Keeping repository as it's used by {len(dependent_knowledge)} other knowledge base(s)")

        # Remove from metadata
        logger.info(f"Removing metadata for '{title}'")
        del container.m[title]

        # Save metadata
        logger.info(f"Saving updated metadata to {settings.meta_path}")
        container.save(settings.meta_path)

        click.echo(f"Successfully deleted knowledge base: {title}")
        return 0
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        click.echo(f"Error: {str(e)}", err=True)
        return 1


if __name__ == "__main__":
    main()  # pragma: no cover
