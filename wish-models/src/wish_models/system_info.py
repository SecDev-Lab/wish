"""System information model."""

from typing import Optional

from pydantic import BaseModel


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
