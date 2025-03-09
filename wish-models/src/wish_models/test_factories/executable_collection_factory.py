from typing import List

import factory

from wish_models.executable_collection import ExecutableCollection
from wish_models.test_factories.executable_info_factory import ExecutableInfoFactory


class ExecutableCollectionFactory(factory.Factory):
    """Factory for creating ExecutableCollection instances for testing."""

    class Meta:
        model = ExecutableCollection

    executables = factory.List([
        factory.SubFactory(ExecutableInfoFactory, path="/usr/bin/test1"),
        factory.SubFactory(ExecutableInfoFactory, path="/usr/bin/test2"),
        factory.SubFactory(ExecutableInfoFactory, path="/usr/local/bin/test3")
    ])

    @classmethod
    def create_with_executables(cls, executable_paths: List[str]) -> ExecutableCollection:
        """Create an ExecutableCollection with the specified executable paths."""
        collection = ExecutableCollection()
        for path in executable_paths:
            collection.add_executable(path)
        return collection

    @classmethod
    def create_with_directory_structure(cls, directory_structure: dict) -> ExecutableCollection:
        """
        Create an ExecutableCollection with a specified directory structure.

        Args:
            directory_structure: A dictionary where keys are directories and values are lists of filenames
                                Example: {"/usr/bin": ["ls", "grep"], "/usr/local/bin": ["python"]}

        Returns:
            ExecutableCollection: A collection with the specified directory structure
        """
        collection = ExecutableCollection()
        for directory, filenames in directory_structure.items():
            for filename in filenames:
                collection.add_executable(
                    path=f"{directory}/{filename}",
                    size=12345,
                    permissions="rwxr-xr-x"
                )
        return collection
