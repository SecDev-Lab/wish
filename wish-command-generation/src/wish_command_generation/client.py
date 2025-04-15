"""Client for the command generation API."""

import json
import logging
from typing import Any, Dict, List, Optional

import requests

from .config import ClientConfig
from .exceptions import CommandGenerationError
from .models import GeneratedCommand, GenerateRequest, GenerateResponse

# Configure logging
logger = logging.getLogger(__name__)


class CommandGenerationClient:
    """Client for the command generation API."""

    def __init__(self, config: Optional[ClientConfig] = None):
        """Initialize the client.

        Args:
            config: Configuration for the client. If None, load from environment variables.
        """
        self.config = config or ClientConfig.from_env()
        logger.debug(f"Initialized CommandGenerationClient with API URL: {self.config.api_base_url}")

    def generate_commands(self, wish_obj, system_info=None) -> List[Dict[str, str]]:
        """Generate commands based on a wish object.

        Args:
            wish_obj: The wish object containing the query.
            system_info: Optional system information for command generation.

        Returns:
            A list of command inputs, each containing a command and explanation.

        Raises:
            CommandGenerationError: If there is an error generating commands.
        """
        try:
            # Extract the query from the wish object
            query = wish_obj.wish

            # Create context from system_info
            context = {}
            if system_info:
                context["system_info"] = system_info.to_dict() if hasattr(system_info, "to_dict") else system_info

            # Generate command using the API
            response = self.generate_command(query, context)

            # Check for errors
            if response.error:
                raise CommandGenerationError(f"Error generating command: {response.error}", str(response))

            # Create command inputs
            command_inputs = [{
                "command": (
                    response.generated_command["command"]
                    if isinstance(response.generated_command, dict)
                    else response.generated_command.command
                ),
                "explanation": (
                    response.generated_command["explanation"]
                    if isinstance(response.generated_command, dict)
                    else response.generated_command.explanation
                )
            }]

            return command_inputs
        except Exception as e:
            # Wrap any exceptions in CommandGenerationError
            if isinstance(e, CommandGenerationError):
                raise
            # No API response for general exceptions
            raise CommandGenerationError(f"Error generating commands: {str(e)}", None) from e

    def generate_command(
        self, query: str, context: Optional[Dict[str, Any]] = None
    ) -> GenerateResponse:
        """Generate a command based on a natural language query.

        Args:
            query: The natural language query to generate a command for.
            context: Optional context information for command generation.

        Returns:
            The generated command with explanation.

        Raises:
            requests.RequestException: If there is an error communicating with the API.
            ValueError: If the API returns an invalid response.
        """
        # Create the request
        request = GenerateRequest(
            query=query,
            context=context or {}
        )

        try:
            # Send the request to the API
            logger.debug(f"Sending request to {self.config.generate_endpoint}")
            response = requests.post(
                self.config.generate_endpoint,
                json=request.model_dump(),
                headers={"Content-Type": "application/json"}
            )

            # Check for HTTP errors
            response.raise_for_status()

            # Parse the response
            data = response.json()
            if "generated_command" in data and isinstance(data["generated_command"], dict):
                # 辞書を明示的にGeneratedCommandオブジェクトに変換
                data["generated_command"] = GeneratedCommand(**data["generated_command"])
            return GenerateResponse.model_validate(data)

        except requests.RequestException as e:
            logger.error(f"Error communicating with API: {e}")
            # Create a fallback response with the error
            return GenerateResponse(
                generated_command=GeneratedCommand(
                    command="echo 'Command generation failed'",
                    explanation=f"Error: Failed to generate command due to API error: {str(e)}"
                ),
                error=str(e)
            )
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Error parsing API response: {e}")
            # Create a fallback response with the error
            return GenerateResponse(
                generated_command=GeneratedCommand(
                    command="echo 'Command generation failed'",
                    explanation=f"Error: Failed to parse API response: {str(e)}"
                ),
                error=str(e)
            )


# Convenience function for generating commands
def generate_command(
    query: str,
    context: Optional[Dict[str, Any]] = None,
    config: Optional[ClientConfig] = None
) -> GenerateResponse:
    """Generate a command based on a natural language query.

    Args:
        query: The natural language query to generate a command for.
        context: Optional context information for command generation.
        config: Optional configuration for the client.

    Returns:
        The generated command with explanation.
    """
    client = CommandGenerationClient(config)
    return client.generate_command(query, context)
