"""Factory for creating SystemInfoCollector instances for testing."""

import factory
from unittest.mock import AsyncMock, MagicMock

from wish_models.system_info import SystemInfo
from wish_models.executable_collection import ExecutableCollection
from wish_models.test_factories.system_info_factory import SystemInfoFactory
from wish_models.test_factories.executable_collection_factory import ExecutableCollectionFactory

from wish_command_execution.system_info import SystemInfoCollector


class SystemInfoCollectorFactory(factory.Factory):
    """Factory for creating SystemInfoCollector instances."""

    class Meta:
        model = SystemInfoCollector

    backend = factory.LazyFunction(lambda: MagicMock())

    @classmethod
    def create_with_mocks(cls, system_info=None, executables=None, **kwargs):
        """Create a SystemInfoCollector with mocked methods.

        Args:
            system_info: SystemInfo to return from collect_system_info.
            executables: ExecutableCollection to return from collect_executables.
            **kwargs: Additional attributes to set on the collector.

        Returns:
            SystemInfoCollector: A configured SystemInfoCollector instance with mocks.
        """
        collector = cls.create(**kwargs)
        
        # Create default objects if not provided
        if system_info is None:
            system_info = SystemInfoFactory.create()
        if executables is None:
            executables = ExecutableCollectionFactory.create()
        
        # Mock methods
        collector.collect_system_info = AsyncMock(return_value=system_info)
        
        # Mock static methods
        SystemInfoCollector.collect_system_info_sync = MagicMock(return_value=system_info)
        SystemInfoCollector.collect_basic_info_from_session = AsyncMock(return_value=system_info)
        SystemInfoCollector.collect_executables_from_session = AsyncMock(return_value=executables)
        SystemInfoCollector.collect_from_session = AsyncMock(return_value=(system_info, executables))
        
        return collector
