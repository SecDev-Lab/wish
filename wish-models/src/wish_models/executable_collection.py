"""Executable collection model."""

from typing import Dict, List, Optional

from pydantic import BaseModel

from wish_models.executable_info import ExecutableInfo


class ExecutableCollection(BaseModel):
    """Collection of executable files, grouped by directory."""
    executables: List[ExecutableInfo] = []

    def group_by_directory(self) -> Dict[str, List[ExecutableInfo]]:
        """Group executables by their directory."""
        result: Dict[str, List[ExecutableInfo]] = {}

        for exe in self.executables:
            directory = exe.directory
            if directory not in result:
                result[directory] = []
            result[directory].append(exe)

        return result

    def add_executable(self, path: str, size: Optional[int] = None, permissions: Optional[str] = None) -> None:
        """Add an executable to the collection."""
        self.executables.append(ExecutableInfo(
            path=path,
            size=size,
            permissions=permissions
        ))
