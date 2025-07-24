"""Knowledge base manager for initialization and updates."""

import asyncio
import logging
from collections.abc import Callable
from typing import Any

from .config import KnowledgeConfig
from .exceptions import WishKnowledgeError
from .sources import HackTricksSource
from .storage import MetadataStorage

logger = logging.getLogger(__name__)


class KnowledgeManager:
    """Manages knowledge base initialization and updates."""

    def __init__(self, config: KnowledgeConfig | None = None) -> None:
        """Initialize knowledge manager."""
        self.config = config or KnowledgeConfig()
        self.metadata_storage = MetadataStorage(self.config)
        self._import_task: asyncio.Task[Any] | None = None
        self._import_complete = False

    async def initialize(self, progress_callback: Callable[[str, float], None] | None = None) -> bool:
        """Initialize knowledge base with auto-import if enabled (background mode)."""
        self.config.progress_callback = progress_callback

        # Check if already initialized
        metadata = self.metadata_storage.load_metadata()
        if metadata.get("initialized", False):
            logger.info("Knowledge base already initialized")
            self._import_complete = True
            return True

        # Check if auto-import is enabled
        if not self.config.auto_import:
            logger.info("Auto-import disabled, skipping initialization")
            return False

        # Start import in background
        logger.info("Starting background import of HackTricks knowledge...")
        self._import_task = asyncio.create_task(self._import_knowledge())

        return True

    async def initialize_foreground(self, progress_callback: Callable[[str, float], None] | None = None) -> bool:
        """Initialize knowledge base in foreground (blocking mode)."""
        self.config.progress_callback = progress_callback

        # Check if already initialized
        metadata = self.metadata_storage.load_metadata()
        if metadata.get("initialized", False):
            logger.info("Knowledge base already initialized")
            self._import_complete = True
            return True

        # Check if auto-import is enabled
        if not self.config.auto_import:
            logger.info("Auto-import disabled, skipping initialization")
            return False

        # Run import directly (not as background task)
        logger.info("Running foreground import of HackTricks knowledge...")
        await self._import_knowledge()

        return self._import_complete

    async def _import_knowledge(self) -> None:
        """Import knowledge from all configured sources."""
        try:
            # Currently only HackTricks is supported
            if "hacktricks" in self.config.sources and self.config.hacktricks.enabled:
                source = HackTricksSource(self.config)
                result = await source.process_and_store()

                if result["status"] == "success":
                    # Mark as initialized
                    self.metadata_storage.update_metadata(
                        {
                            "initialized": True,
                            "import_result": result,
                        }
                    )
                    self._import_complete = True
                    logger.info(f"Knowledge import completed: {result}")
                else:
                    logger.warning(f"Knowledge import completed with status: {result['status']}")

        except Exception as e:
            logger.error(f"Failed to import knowledge: {e}")
            raise WishKnowledgeError(f"Knowledge import failed: {e}") from e

    async def wait_for_import(self, timeout: float | None = None) -> bool:
        """Wait for import to complete."""
        if self._import_complete:
            return True

        if not self._import_task:
            return False

        try:
            await asyncio.wait_for(self._import_task, timeout=timeout)
            return self._import_complete
        except TimeoutError:
            logger.warning("Import timeout reached")
            return False
        except Exception as e:
            logger.error(f"Import failed: {e}")
            return False

    def is_import_complete(self) -> bool:
        """Check if import is complete."""
        return self._import_complete

    def get_import_progress(self) -> dict[str, Any]:
        """Get current import progress."""
        if self._import_complete:
            return {"status": "complete", "progress": 100.0}

        if not self._import_task:
            return {"status": "not_started", "progress": 0.0}

        if self._import_task.done():
            return {"status": "complete", "progress": 100.0}

        # TODO: Implement more detailed progress tracking
        return {"status": "in_progress", "progress": 50.0}

    async def update_knowledge(self, force: bool = False) -> dict[str, Any]:
        """Update knowledge base."""
        if not force and not self.metadata_storage.should_update():
            logger.info("Knowledge base is up to date")
            return {"status": "up_to_date"}

        # Run update
        if "hacktricks" in self.config.sources and self.config.hacktricks.enabled:
            source = HackTricksSource(self.config)
            result = await source.process_and_store()
            return result

        return {"status": "no_sources"}

    def reset_knowledge(self) -> None:
        """Reset the entire knowledge base."""
        logger.warning("Resetting knowledge base...")

        # Clear vector store
        from .vectorstore import ChromaDBStore

        vectorstore = ChromaDBStore(self.config)
        vectorstore.reset()

        # Clear TSV files
        tools_tsv = self.config.get_tools_tsv_path()
        if tools_tsv.exists():
            tools_tsv.unlink()

        # Clear metadata
        metadata_path = self.config.get_metadata_path()
        if metadata_path.exists():
            metadata_path.unlink()

        # Clear cache
        from .storage import CacheStorage

        cache = CacheStorage(self.config)
        cache.clear_cache()

        self._import_complete = False
        logger.info("Knowledge base reset complete")


def check_knowledge_initialized() -> bool:
    """Quick check if knowledge base is initialized."""
    config = KnowledgeConfig()
    metadata_path = config.get_metadata_path()

    if not metadata_path.exists():
        return False

    try:
        storage = MetadataStorage(config)
        metadata = storage.load_metadata()
        return metadata.get("initialized", False)
    except Exception:
        return False
