"""Auto-save management for wish-core state persistence."""

import asyncio
import logging
from collections.abc import Callable
from datetime import datetime

from wish_models import EngagementState

from .session_store import SessionStore


class AutoSaveManager:
    """Auto-save manager for periodic state persistence."""

    def __init__(
        self,
        session_store: SessionStore,
        save_interval: int = 30,
        state_provider: Callable[[], EngagementState] | None = None,
    ) -> None:
        """Initialize auto-save manager.

        Args:
            session_store: SessionStore instance for persistence
            save_interval: Save interval in seconds (default: 30)
            state_provider: Callable that returns current EngagementState
        """
        self.session_store = session_store
        self.save_interval = save_interval
        self.state_provider = state_provider
        self.logger = logging.getLogger(__name__)

        self._auto_save_task: asyncio.Task[None] | None = None
        self._is_running = False
        self._last_save_time = datetime.now()
        self._changes_since_save = False

    async def start_auto_save(self) -> None:
        """Start the auto-save background task."""
        if self._is_running:
            return

        self._is_running = True
        self._auto_save_task = asyncio.create_task(self._auto_save_loop())
        self.logger.info(f"Auto-save started with {self.save_interval}s interval")

    async def stop_auto_save(self) -> None:
        """Stop the auto-save background task."""
        self._is_running = False

        if self._auto_save_task:
            self._auto_save_task.cancel()
            try:
                await self._auto_save_task
            except asyncio.CancelledError:
                pass

        # Final save if there are pending changes
        if self._changes_since_save:
            await self._perform_save()

        self.logger.info("Auto-save stopped")

    def mark_changes(self) -> None:
        """Mark that changes have occurred since last save."""
        self._changes_since_save = True

    async def force_save(self) -> bool:
        """Force an immediate save operation.

        Returns:
            True if save was successful, False otherwise
        """
        return await self._perform_save()

    def set_state_provider(self, state_provider: Callable[[], EngagementState]) -> None:
        """Set or update the state provider callback."""
        self.state_provider = state_provider

    @property
    def is_running(self) -> bool:
        """Check if auto-save is currently running."""
        return self._is_running

    @property
    def last_save_time(self) -> datetime:
        """Get the timestamp of the last successful save."""
        return self._last_save_time

    @property
    def has_unsaved_changes(self) -> bool:
        """Check if there are unsaved changes."""
        return self._changes_since_save

    async def _auto_save_loop(self) -> None:
        """Main auto-save loop that runs in the background."""
        while self._is_running:
            try:
                await asyncio.sleep(self.save_interval)

                if self._changes_since_save:
                    await self._perform_save()

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Auto-save error: {e}")
                # Continue running even after errors
                await asyncio.sleep(5)

    async def _perform_save(self) -> bool:
        """Execute the save operation.

        Returns:
            True if save was successful, False otherwise
        """
        if not self.state_provider:
            self.logger.warning("No state provider configured for auto-save")
            return False

        try:
            current_state = self.state_provider()
            if current_state:
                await self.session_store.save_current_session(current_state)
                self._last_save_time = datetime.now()
                self._changes_since_save = False
                self.logger.debug("Auto-save completed successfully")
                return True
        except Exception as e:
            self.logger.error(f"Save operation failed: {e}")

        return False
