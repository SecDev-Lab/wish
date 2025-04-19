"""Lambda handler for the wish-log-analysis-api."""

import json
import logging
from typing import Any, Dict

from wish_models.settings import Settings, get_default_env_path

from .core.analyzer import analyze_command_result
from .models import AnalyzeRequest

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """AWS Lambda handler for the wish-log-analysis-api.

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
        request = AnalyzeRequest.model_validate(body)

        # Analyze the command result
        response = analyze_command_result(request, settings_obj=settings)

        # Check if there was an error during analysis
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
