"""Factory for creating backends."""

from typing import Callable, Optional, Union

from pydantic import BaseModel
from wish_models import LogFiles

from wish_command_execution.backend.base import Backend
from wish_command_execution.backend.bash import BashBackend


class BashConfig(BaseModel):
    """Configuration for bash backend."""
    shell_path: str = "/bin/bash"
    log_summarizer: Optional[Callable[[LogFiles], str]] = None


class SliverConfig(BaseModel):
    """Configuration for Sliver backend."""
    session_id: str
    client_config_path: str


def create_backend(config: Union[BashConfig, SliverConfig]) -> Backend:
    """Create a backend based on the configuration.

    Args:
        config: The backend configuration.

    Returns:
        A backend instance.
    """
    if isinstance(config, BashConfig):
        return BashBackend(log_summarizer=config.log_summarizer)
    elif isinstance(config, SliverConfig):
        # Future implementation
        raise NotImplementedError("Sliver backend not implemented yet")
    else:
        raise ValueError(f"Unsupported backend configuration: {type(config)}")
