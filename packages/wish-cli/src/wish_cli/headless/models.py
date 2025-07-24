"""Models for headless mode."""

from dataclasses import dataclass
from typing import Any

from wish_models.engagement import EngagementState


@dataclass
class PromptResult:
    """Result of a prompt execution."""

    prompt: str
    result: Any
    state_before: EngagementState
    state_after: EngagementState
    execution_time: float


@dataclass
class SessionSummary:
    """Summary of a completed session."""

    session_id: str
    duration: float
    prompts_executed: int
    hosts_discovered: int
    findings: int
