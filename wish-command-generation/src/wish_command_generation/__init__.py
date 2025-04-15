"""Command generation client for wish."""

from .client import CommandGenerationClient as CommandGenerator
from .client import generate_command
from .config import ClientConfig
from .exceptions import CommandGenerationError
from .models import GeneratedCommand, GenerateRequest, GenerateResponse
