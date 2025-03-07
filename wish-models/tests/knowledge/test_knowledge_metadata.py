"""Tests for knowledge metadata models."""

from datetime import datetime, timezone
from pathlib import Path

from wish_models.knowledge.knowledge_metadata import KnowledgeMetadata, KnowledgeMetadataContainer
from wish_models.utc_datetime import UtcDatetime


class TestKnowledgeMetadata:
    """Test for KnowledgeMetadata."""

    def test_from_json_to_json(self):
        """Test conversion between JSON and KnowledgeMetadata."""
        # Create a KnowledgeMetadata instance
        metadata = KnowledgeMetadata(
            title="Test Knowledge",
            repo_url="https://github.com/test/repo",
            glob_pattern="**/*.md",
            repo_path=Path("/tmp/test"),
            created_at=UtcDatetime(datetime(2023, 1, 1, tzinfo=timezone.utc)),
            updated_at=UtcDatetime(datetime(2023, 1, 1, tzinfo=timezone.utc))
        )

        # Convert to JSON
        metadata_json = metadata.to_json()

        # Convert back to KnowledgeMetadata
        metadata2 = KnowledgeMetadata.from_json(metadata_json)

        # Check if they are equal
        assert metadata.title == metadata2.title
        assert metadata.repo_url == metadata2.repo_url
        assert metadata.glob_pattern == metadata2.glob_pattern
        assert str(metadata.repo_path) == str(metadata2.repo_path)
        assert metadata.created_at.v == metadata2.created_at.v
        assert metadata.updated_at.v == metadata2.updated_at.v

    def test_from_dict_to_dict(self):
        """Test conversion between dict and KnowledgeMetadata."""
        # Create a KnowledgeMetadata instance
        metadata = KnowledgeMetadata(
            title="Test Knowledge",
            repo_url="https://github.com/test/repo",
            glob_pattern="**/*.md",
            repo_path=Path("/tmp/test"),
            created_at=UtcDatetime(datetime(2023, 1, 1, tzinfo=timezone.utc)),
            updated_at=UtcDatetime(datetime(2023, 1, 1, tzinfo=timezone.utc))
        )

        # Convert to dict
        metadata_dict = metadata.to_dict()

        # Convert back to KnowledgeMetadata
        metadata2 = KnowledgeMetadata.from_dict(metadata_dict)

        # Check if they are equal
        assert metadata.title == metadata2.title
        assert metadata.repo_url == metadata2.repo_url
        assert metadata.glob_pattern == metadata2.glob_pattern
        assert str(metadata.repo_path) == str(metadata2.repo_path)
        assert metadata.created_at.v == metadata2.created_at.v
        assert metadata.updated_at.v == metadata2.updated_at.v


class TestKnowledgeMetadataContainer:
    """Test for KnowledgeMetadataContainer."""

    def test_add_get(self):
        """Test add and get methods."""
        # Create a KnowledgeMetadataContainer instance
        container = KnowledgeMetadataContainer()

        # Create a KnowledgeMetadata instance
        metadata = KnowledgeMetadata(
            title="Test Knowledge",
            repo_url="https://github.com/test/repo",
            glob_pattern="**/*.md",
            repo_path=Path("/tmp/test"),
            created_at=UtcDatetime(datetime(2023, 1, 1, tzinfo=timezone.utc)),
            updated_at=UtcDatetime(datetime(2023, 1, 1, tzinfo=timezone.utc))
        )

        # Add metadata to container
        container.add(metadata)

        # Get metadata from container
        metadata2 = container.get("Test Knowledge")

        # Check if they are equal
        assert metadata.title == metadata2.title
        assert metadata.repo_url == metadata2.repo_url
        assert metadata.glob_pattern == metadata2.glob_pattern
        assert str(metadata.repo_path) == str(metadata2.repo_path)
        assert metadata.created_at.v == metadata2.created_at.v
        assert metadata.updated_at.v == metadata2.updated_at.v

    def test_save_load(self, tmp_path):
        """Test save and load methods."""
        # Create a KnowledgeMetadataContainer instance
        container = KnowledgeMetadataContainer()

        # Create a KnowledgeMetadata instance
        metadata = KnowledgeMetadata(
            title="Test Knowledge",
            repo_url="https://github.com/test/repo",
            glob_pattern="**/*.md",
            repo_path=Path("/tmp/test"),
            created_at=UtcDatetime(datetime(2023, 1, 1, tzinfo=timezone.utc)),
            updated_at=UtcDatetime(datetime(2023, 1, 1, tzinfo=timezone.utc))
        )

        # Add metadata to container
        container.add(metadata)

        # Save container to file
        meta_path = tmp_path / "meta.json"
        container.save(meta_path)

        # Load container from file
        container2 = KnowledgeMetadataContainer.load(meta_path)

        # Get metadata from container
        metadata2 = container2.get("Test Knowledge")

        # Check if they are equal
        assert metadata.title == metadata2.title
        assert metadata.repo_url == metadata2.repo_url
        assert metadata.glob_pattern == metadata2.glob_pattern
        assert str(metadata.repo_path) == str(metadata2.repo_path)
        assert metadata.created_at.v == metadata2.created_at.v
        assert metadata.updated_at.v == metadata2.updated_at.v

    def test_from_json_to_json(self):
        """Test conversion between JSON and KnowledgeMetadataContainer."""
        # Create a KnowledgeMetadataContainer instance
        container = KnowledgeMetadataContainer()

        # Create a KnowledgeMetadata instance
        metadata = KnowledgeMetadata(
            title="Test Knowledge",
            repo_url="https://github.com/test/repo",
            glob_pattern="**/*.md",
            repo_path=Path("/tmp/test"),
            created_at=UtcDatetime(datetime(2023, 1, 1, tzinfo=timezone.utc)),
            updated_at=UtcDatetime(datetime(2023, 1, 1, tzinfo=timezone.utc))
        )

        # Add metadata to container
        container.add(metadata)

        # Convert to JSON
        container_json = container.to_json()

        # Convert back to KnowledgeMetadataContainer
        container2 = KnowledgeMetadataContainer.from_json(container_json)

        # Get metadata from container
        metadata2 = container2.get("Test Knowledge")

        # Check if they are equal
        assert metadata.title == metadata2.title
        assert metadata.repo_url == metadata2.repo_url
        assert metadata.glob_pattern == metadata2.glob_pattern
        assert str(metadata.repo_path) == str(metadata2.repo_path)
        assert metadata.created_at.v == metadata2.created_at.v
        assert metadata.updated_at.v == metadata2.updated_at.v

    def test_from_dict_to_dict(self):
        """Test conversion between dict and KnowledgeMetadataContainer."""
        # Create a KnowledgeMetadataContainer instance
        container = KnowledgeMetadataContainer()

        # Create a KnowledgeMetadata instance
        metadata = KnowledgeMetadata(
            title="Test Knowledge",
            repo_url="https://github.com/test/repo",
            glob_pattern="**/*.md",
            repo_path=Path("/tmp/test"),
            created_at=UtcDatetime(datetime(2023, 1, 1, tzinfo=timezone.utc)),
            updated_at=UtcDatetime(datetime(2023, 1, 1, tzinfo=timezone.utc))
        )

        # Add metadata to container
        container.add(metadata)

        # Convert to dict
        container_dict = container.to_dict()

        # Convert back to KnowledgeMetadataContainer
        container2 = KnowledgeMetadataContainer.from_dict(container_dict)

        # Get metadata from container
        metadata2 = container2.get("Test Knowledge")

        # Check if they are equal
        assert metadata.title == metadata2.title
        assert metadata.repo_url == metadata2.repo_url
        assert metadata.glob_pattern == metadata2.glob_pattern
        assert str(metadata.repo_path) == str(metadata2.repo_path)
        assert metadata.created_at.v == metadata2.created_at.v
        assert metadata.updated_at.v == metadata2.updated_at.v
