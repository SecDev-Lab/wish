"""Command generation client for wish."""

from .client import CommandGenerationClient as CommandGenerator
from .client import generate_command
from .config import ClientConfig
from .models import GenerateRequest, GenerateResponse, GeneratedCommand
from .exceptions import CommandGenerationError
