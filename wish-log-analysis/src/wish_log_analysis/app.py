"""Client for the wish-log-analysis-api."""

import json
import logging
import os
import requests
from typing import Optional

from wish_models.command_result import CommandResult

# Configure logging
logger = logging.getLogger(__name__)


class LogAnalysisClient:
    """Client for the wish-log-analysis-api."""

    def __init__(self, api_url: Optional[str] = None):
        """Initialize the client.

        Args:
            api_url: The URL of the API. If not provided, will use the WISH_LOG_ANALYSIS_API_URL
                environment variable, or default to http://localhost:3000/analyze.
        """
        self.api_url = api_url or os.environ.get(
            "WISH_LOG_ANALYSIS_API_URL", "http://localhost:3000/analyze"
        )
        logger.info(f"Initialized LogAnalysisClient with API URL: {self.api_url}")

    def analyze(self, command_result: CommandResult) -> CommandResult:
        """Analyze a command result.

        Args:
            command_result: The command result to analyze.

        Returns:
            The analyzed command result.

        Raises:
            Exception: If the API request fails.
        """
        try:
            # Prepare the request
            payload = {
                "command_result": command_result.model_dump()
            }

            # Make the request
            logger.info(f"Sending request to {self.api_url}")
            response = requests.post(
                self.api_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30,
            )

            # Check for errors
            response.raise_for_status()

            # Parse the response
            data = response.json()
            if "error" in data and data["error"]:
                raise Exception(f"API error: {data['error']}")

            # Return the analyzed command result
            return CommandResult.model_validate(data["analyzed_command_result"])

        except requests.RequestException as e:
            logger.exception(f"Request failed: {e}")
            # Return the original command result if the API request fails
            return command_result
        except Exception as e:
            logger.exception(f"Error analyzing command result: {e}")
            # Return the original command result if there's an error
            return command_result


# For backwards compatibility
def analyze_command_result(command_result: CommandResult) -> CommandResult:
    """Analyze a command result.

    Args:
        command_result: The command result to analyze.

    Returns:
        The analyzed command result.
    """
    client = LogAnalysisClient()
    return client.analyze(command_result)
