"""Path utilities."""

import os
from pathlib import Path


def ensure_directory_exists(path: Path) -> None:
    """Ensure that a directory exists.

    Args:
        path: Path to the directory
    """
    path.mkdir(parents=True, exist_ok=True)


def expand_user_path(path: str) -> Path:
    """Expand user path (e.g., "~/foo" to "/home/user/foo").

    Args:
        path: Path string

    Returns:
        Expanded path
    """
    return Path(os.path.expanduser(path))
