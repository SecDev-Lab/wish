"""
wish-models: Core data models and validation for wish

This package provides type-safe data models and validation logic
for the wish penetration testing command center.
"""

from .data import CollectedData
from .engagement import EngagementState, Target
from .finding import Finding
from .host import Host, Service, SMBInfo, SMBShare
from .session import SessionMetadata
from .validation import ValidationError, ValidationResult

# Rebuild models to resolve forward references
EngagementState.model_rebuild()
Host.model_rebuild()
Service.model_rebuild()
SMBInfo.model_rebuild()
SMBShare.model_rebuild()
Finding.model_rebuild()
CollectedData.model_rebuild()
Target.model_rebuild()
SessionMetadata.model_rebuild()

__all__ = [
    "EngagementState",
    "Target",
    "Host",
    "Service",
    "SMBInfo",
    "SMBShare",
    "Finding",
    "CollectedData",
    "SessionMetadata",
    "ValidationError",
    "ValidationResult",
]

__version__ = "0.1.0"
