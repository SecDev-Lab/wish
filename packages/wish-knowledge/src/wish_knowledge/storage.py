"""Storage implementations for knowledge base."""

import json
import logging
from datetime import datetime
from typing import Any

from .config import KnowledgeConfig
from .exceptions import StorageError

logger = logging.getLogger(__name__)


class MetadataStorage:
    """Storage for knowledge base metadata."""

    def __init__(self, config: KnowledgeConfig) -> None:
        """Initialize metadata storage."""
        self.config = config
        self.metadata_path = config.get_metadata_path()

    def save_metadata(self, metadata: dict[str, Any]) -> None:
        """Save metadata to JSON file."""
        try:
            # Add timestamp
            metadata["last_updated"] = datetime.utcnow().isoformat()

            with open(self.metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved metadata to {self.metadata_path}")

        except Exception as e:
            raise StorageError(f"Failed to save metadata: {e}") from e

    def load_metadata(self) -> dict[str, Any]:
        """Load metadata from JSON file."""
        if not self.metadata_path.exists():
            return {}

        try:
            with open(self.metadata_path, encoding="utf-8") as f:
                result = json.load(f)
                return result if isinstance(result, dict) else {}
        except Exception as e:
            logger.warning(f"Failed to load metadata: {e}")
            return {}

    def update_metadata(self, updates: dict[str, Any]) -> None:
        """Update specific metadata fields."""
        metadata = self.load_metadata()
        metadata.update(updates)
        self.save_metadata(metadata)

    def get_last_update_time(self) -> datetime | None:
        """Get last update time from metadata."""
        metadata = self.load_metadata()
        if "last_updated" in metadata:
            try:
                return datetime.fromisoformat(metadata["last_updated"])
            except ValueError:
                pass
        return None

    def should_update(self) -> bool:
        """Check if knowledge base should be updated."""
        last_update = self.get_last_update_time()
        if not last_update:
            return True

        # Check if update interval has passed
        days_since_update = (datetime.utcnow() - last_update).days
        return days_since_update >= self.config.update_interval_days


class CacheStorage:
    """Storage for cached HackTricks content."""

    def __init__(self, config: KnowledgeConfig) -> None:
        """Initialize cache storage."""
        self.config = config
        self.cache_dir = config.get_cache_path()

    def save_page(self, url: str, content: str) -> None:
        """Save a page to cache."""
        # Create safe filename from URL
        safe_name = url.replace("https://", "").replace("/", "_").replace(".", "_")
        cache_file = self.cache_dir / f"{safe_name}.md"

        try:
            cache_file.write_text(content, encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to cache page {url}: {e}")

    def load_page(self, url: str) -> str | None:
        """Load a page from cache."""
        safe_name = url.replace("https://", "").replace("/", "_").replace(".", "_")
        cache_file = self.cache_dir / f"{safe_name}.md"

        if cache_file.exists():
            try:
                return cache_file.read_text(encoding="utf-8")
            except Exception as e:
                logger.warning(f"Failed to load cached page {url}: {e}")

        return None

    def clear_cache(self) -> None:
        """Clear all cached pages."""
        try:
            for cache_file in self.cache_dir.glob("*.md"):
                cache_file.unlink()
            logger.info("Cache cleared")
        except Exception as e:
            logger.warning(f"Failed to clear cache: {e}")
