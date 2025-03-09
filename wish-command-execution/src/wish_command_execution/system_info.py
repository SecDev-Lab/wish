"""System information collector."""

import asyncio
import logging
from typing import TypeVar

from wish_models.system_info import SystemInfo

# Type variable for backend
B = TypeVar('B')


class SystemInfoCollector:
    """Collector for system information using backends."""

    def __init__(self, backend: B):
        """Initialize the system information collector.

        Args:
            backend: Backend to use for collecting system information
        """
        self.backend = backend

    async def collect_system_info(self, collect_system_executables: bool = False) -> SystemInfo:
        """Collect system information using the backend.

        Args:
            collect_system_executables: Whether to collect executables from the entire system

        Returns:
            SystemInfo: Collected system information
        """
        try:
            # Call the backend's get_system_info method
            return await self.backend.get_system_info(collect_system_executables)
        except Exception as e:
            logging.error(f"Error collecting system info: {str(e)}")
            # Return minimal SystemInfo on error
            return SystemInfo(
                os="Unknown (Error)",
                arch="Unknown",
                hostname="Unknown",
                username="Unknown",
                version=f"Error: {str(e)}"
            )

    @staticmethod
    def collect_system_info_sync(backend: B, collect_system_executables: bool = False) -> SystemInfo:
        """Synchronously collect system information using the backend.

        This is a convenience method that wraps the async collect_system_info method.

        Args:
            backend: Backend to use for collecting system information
            collect_system_executables: Whether to collect executables from the entire system

        Returns:
            SystemInfo: Collected system information
        """
        collector = SystemInfoCollector(backend)
        try:
            # Get existing event loop or create a new one
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(collector.collect_system_info(collect_system_executables))
        except RuntimeError:
            # If no event loop exists, create a new one
            return asyncio.run(collector.collect_system_info(collect_system_executables))
