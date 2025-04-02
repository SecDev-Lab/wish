"""Lambda handler for the wish-log-analysis-api."""

import json
import logging
from typing import Any, Dict

from .graph import create_log_analysis_graph
from .models import AnalyzeRequest, AnalyzeResponse, GraphState

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def analyze_command_result(request: AnalyzeRequest) -> AnalyzeResponse:
    """Analyze a command result using the log analysis graph.

    Args:
        request: The request containing the command result to analyze.

    Returns:
        The response containing the analyzed command result.
    """
    try:
        # Create the graph
        graph = create_log_analysis_graph()

        # Create the initial state
        initial_state = GraphState(command_result=request.command_result)

        # Run the graph
        result = graph.invoke(initial_state)

        # Return the response
        return AnalyzeResponse(
            analyzed_command_result=result.analyzed_command_result
        )
    except Exception as e:
        logger.exception("Error analyzing command result")
        return AnalyzeResponse(
            analyzed_command_result=request.command_result,
            error=str(e)
        )


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
        # Parse the request body
        body = json.loads(event.get("body", "{}"))
        request = AnalyzeRequest.model_validate(body)

        # Analyze the command result
        response = analyze_command_result(request)

        # Return the response
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
