"""Exceptions for wish-knowledge package."""


class WishKnowledgeError(Exception):
    """Base exception for wish-knowledge package."""

    pass


class KnowledgeSourceError(WishKnowledgeError):
    """Error in knowledge source operations."""

    pass


class ExtractionError(WishKnowledgeError):
    """Error during data extraction."""

    pass


class StorageError(WishKnowledgeError):
    """Error in storage operations."""

    pass


class EmbeddingError(WishKnowledgeError):
    """Error in embedding operations."""

    pass
