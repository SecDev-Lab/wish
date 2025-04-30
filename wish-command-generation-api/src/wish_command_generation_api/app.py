"""Lambda handler for the wish-command-generation-api."""

import json
import logging
from typing import Any, Dict

from wish_models.settings import Settings, get_default_env_path

from .core.generator import generate_commands
from .models import GenerateRequest

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """AWS Lambda handler for the wish-command-generation-api.

    Args:
        event: The Lambda event.
        context: The Lambda context.

    Returns:
        The Lambda response.
    """
    logger.info("Received event: %s", json.dumps(event))

    try:
        # Create settings instance
        env_path = get_default_env_path()
        settings = Settings(env_file=env_path)

        # Parse the request body
        body = json.loads(event.get("body", "{}"))
        request = GenerateRequest.model_validate(body)

        # Generate the commands
        response = generate_commands(request, settings_obj=settings)

        # Check if there was an error during generation
        if response.error is not None:
            return {
                "statusCode": 500,
                "headers": {
                    "Content-Type": "application/json"
                },
                "body": json.dumps({
                    "error": response.error
                })
            }

        # Return the successful response
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps(response.model_dump())
        }
    except Exception as e:
        logger.exception("Error handling request")
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "error": str(e)
            })
        }
