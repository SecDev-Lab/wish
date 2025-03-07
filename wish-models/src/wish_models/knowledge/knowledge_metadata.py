"""Knowledge metadata models."""

import json
from pathlib import Path

from pydantic import BaseModel, Field

from wish_models.utc_datetime import UtcDatetime


class KnowledgeMetadata(BaseModel):
    """Metadata for a knowledge base."""

    title: str
    """Title of the knowledge base."""

    repo_url: str
    """URL of the GitHub repository."""

    repo_license: str | None = None
    """License information of the repository."""

    glob_pattern: str
    """Glob pattern for target files."""

    repo_path: Path
    """Path where the repository is cloned."""

    chunk_size: int = 1000
    """Chunk size for text splitting."""

    chunk_overlap: int = 100
    """Chunk overlap for text splitting."""

    created_at: UtcDatetime
    """Time when the knowledge base was created."""

    updated_at: UtcDatetime
    """Time when the knowledge base was last updated."""

    @classmethod
    def from_json(cls, metadata_json: str) -> "KnowledgeMetadata":
        """Parse JSON string to KnowledgeMetadata.

        Args:
            metadata_json: JSON string representation of KnowledgeMetadata

        Returns:
            KnowledgeMetadata instance
        """
        return cls.model_validate_json(metadata_json)

    @classmethod
    def from_dict(cls, metadata_dict: dict) -> "KnowledgeMetadata":
        """Parse dictionary to KnowledgeMetadata.

        Args:
            metadata_dict: Dictionary representation of KnowledgeMetadata

        Returns:
            KnowledgeMetadata instance
        """
        return cls.model_validate(metadata_dict)

    def to_json(self) -> str:
        """Convert to JSON string.

        Returns:
            JSON string representation of KnowledgeMetadata
        """
        data = self.model_dump()
        data["repo_path"] = str(self.repo_path)
        return json.dumps(data, indent=2)

    def to_dict(self) -> dict:
        """Convert to dictionary.

        Returns:
            Dictionary representation of KnowledgeMetadata
        """
        data = self.model_dump()
        data["repo_path"] = str(self.repo_path)
        return data


class KnowledgeMetadataContainer(BaseModel):
    """Container for knowledge base metadata."""

    m: dict[str, KnowledgeMetadata] = Field(default_factory=dict)
    """Dictionary of knowledge base metadata (key: title)."""

    @classmethod
    def from_json(cls, container_json: str) -> "KnowledgeMetadataContainer":
        """Parse JSON string to KnowledgeMetadataContainer.

        Args:
            container_json: JSON string representation of KnowledgeMetadataContainer

        Returns:
            KnowledgeMetadataContainer instance
        """
        return cls.model_validate_json(container_json)

    @classmethod
    def from_dict(cls, container_dict: dict) -> "KnowledgeMetadataContainer":
        """Parse dictionary to KnowledgeMetadataContainer.

        Args:
            container_dict: Dictionary representation of KnowledgeMetadataContainer

        Returns:
            KnowledgeMetadataContainer instance
        """
        return cls.model_validate(container_dict)

    def to_json(self) -> str:
        """Convert to JSON string.

        Returns:
            JSON string representation of KnowledgeMetadataContainer
        """
        data = {"m": {}}
        for k, v in self.m.items():
            data["m"][k] = v.to_dict()
        return json.dumps(data, indent=2)

    def to_dict(self) -> dict:
        """Convert to dictionary.

        Returns:
            Dictionary representation of KnowledgeMetadataContainer
        """
        data = {"m": {}}
        for k, v in self.m.items():
            data["m"][k] = v.to_dict()
        return data

    @classmethod
    def load(cls, path: Path) -> "KnowledgeMetadataContainer":
        """Load metadata from a JSON file.

        Args:
            path: Path to the JSON file

        Returns:
            KnowledgeMetadataContainer instance
        """
        if not path.exists() or path.stat().st_size == 0:
            return cls()
        try:
            with open(path, "r") as f:
                data = json.load(f)
            return cls.from_dict(data)
        except json.JSONDecodeError:
            # If the file is corrupted, return a new instance
            return cls()

    def save(self, path: Path) -> None:
        """Save metadata to a JSON file.

        Args:
            path: Path to the JSON file
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            f.write(self.to_json())

    def add(self, metadata: KnowledgeMetadata) -> None:
        """Add metadata to the container.

        Args:
            metadata: KnowledgeMetadata to add
        """
        self.m[metadata.title] = metadata

    def get(self, title: str) -> KnowledgeMetadata | None:
        """Get metadata by title.

        Args:
            title: Title of the knowledge base

        Returns:
            KnowledgeMetadata if found, None otherwise
        """
        return self.m.get(title)
