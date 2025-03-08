"""System information models."""

from typing import Dict, List, Optional
from pathlib import Path
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


class SystemInfo(BaseModel):
    """System information model."""
    # OS information
    os: str
    arch: str
    version: Optional[str] = None
    
    # System identification
    hostname: str
    username: str
    uid: Optional[str] = None
    gid: Optional[str] = None
    pid: Optional[int] = None
    
    # Executable files information
    path_executables: ExecutableCollection = ExecutableCollection()
    system_executables: Optional[ExecutableCollection] = None
