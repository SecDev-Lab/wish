import os
from typing import Optional

import factory

from wish_models.executable_info import ExecutableInfo


class ExecutableInfoFactory(factory.Factory):
    """Factory for creating ExecutableInfo instances for testing."""

    class Meta:
        model = ExecutableInfo

    path = "/usr/bin/test-executable"
    size = 12345
    permissions = "rwxr-xr-x"

    @classmethod
    def create_with_directory(cls, directory: str, filename: str,
                             size: Optional[int] = 12345,
                             permissions: Optional[str] = "rwxr-xr-x") -> ExecutableInfo:
        """Create an ExecutableInfo instance with the specified directory and filename."""
        path = os.path.join(directory, filename)
        return ExecutableInfo(
            path=path,
            size=size,
            permissions=permissions
        )
