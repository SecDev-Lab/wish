"""Executable information models."""

from pathlib import Path
from typing import Optional

from pydantic import BaseModel


class ExecutableInfo(BaseModel):
    """Information about an executable file."""
    path: str
    size: Optional[int] = None
    permissions: Optional[str] = None

    @property
    def directory(self) -> str:
        """Get the directory containing this executable."""
        return str(Path(self.path).parent)

    @property
    def filename(self) -> str:
        """Get the filename of this executable."""
        return Path(self.path).name
