"""Lambda handler for the wish-log-analysis-api."""

import json
import logging
import os
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
        
        # Extract the analyzed result
        analyzed_result = None
        
        # Method 1: Access as attribute
        if hasattr(result, "analyzed_command_result") and result.analyzed_command_result is not None:
            analyzed_result = result.analyzed_command_result
        
        # Method 2: Access as dictionary
        elif isinstance(result, dict) and "analyzed_command_result" in result:
            analyzed_result = result["analyzed_command_result"]
        
        # Method 3: Check for AddableValuesDict structure
        elif hasattr(result, "values") and isinstance(result.values, dict) and "analyzed_command_result" in result.values:
            analyzed_result = result.values["analyzed_command_result"]
            
        # Method 4: Get result from the last node
        elif hasattr(result, "result_combiner") and result.result_combiner is not None:
            if hasattr(result.result_combiner, "analyzed_command_result"):
                analyzed_result = result.result_combiner.analyzed_command_result
        
        # If result was found
        if analyzed_result is not None:
            return AnalyzeResponse(
                analyzed_command_result=analyzed_result
            )
        
        # Fallback: If result was not found
        logger.error("Could not find analyzed_command_result in any expected location")
        
        # Create a fallback analyzed_command_result
        from wish_models.command_result import CommandResult
        from wish_models.command_result.command_state import CommandState
        
        fallback_result = CommandResult(
            num=request.command_result.num,
            command=request.command_result.command,
            state=CommandState.API_ERROR,
            exit_code=request.command_result.exit_code,
            log_summary="Error: Failed to analyze command result due to API error",
            log_files=request.command_result.log_files,
            created_at=request.command_result.created_at,
            finished_at=request.command_result.finished_at
        )
        
        return AnalyzeResponse(
            analyzed_command_result=fallback_result,
            error="Failed to generate analyzed_command_result"
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
    
    # Import settings
    from wish_models import settings

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
