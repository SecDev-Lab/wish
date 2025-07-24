"""Event system for wish-core."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from wish_models import CollectedData, Finding, Host


@dataclass
class HostDiscovered:
    """Event for when a host is discovered."""

    host: Host


@dataclass
class FindingAdded:
    """Event for when a finding is added."""

    finding: Finding


@dataclass
class DataCollected:
    """Event for when data is collected."""

    data: CollectedData


@dataclass
class ModeChanged:
    """Event for when engagement mode changes."""

    old_mode: str
    new_mode: str


EngagementEvent = HostDiscovered | FindingAdded | DataCollected | ModeChanged


class EventBus:
    """Event bus for observer pattern implementation."""

    def __init__(self) -> None:
        self._handlers: dict[type, list[Callable[[Any], Awaitable[None]]]] = {}

    def subscribe(self, event_type: type, handler: Callable[[Any], Awaitable[None]]) -> None:
        """Subscribe to an event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    async def publish(self, event: EngagementEvent) -> None:
        """Publish an event to all subscribers."""
        import logging

        logger = logging.getLogger(__name__)

        event_type = type(event)
        if event_type in self._handlers:
            for handler in self._handlers[event_type]:
                try:
                    await handler(event)
                except Exception as e:
                    logger.error(f"Error in event handler: {e}")
                    # Continue with other handlers despite error
