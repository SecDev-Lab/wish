"""Event system for headless mode."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class EventType(Enum):
    """Event types for headless mode."""

    PLAN_APPROVAL_REQUIRED = "plan_approval_required"
    JOB_STARTED = "job_started"
    JOB_PROGRESS = "job_progress"
    JOB_COMPLETED = "job_completed"
    STATE_CHANGED = "state_changed"
    ERROR_OCCURRED = "error_occurred"


@dataclass
class Event:
    """Event data structure."""

    event_type: EventType
    data: dict[str, Any]
    timestamp: datetime
    requires_response: bool = False
