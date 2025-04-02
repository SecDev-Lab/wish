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

        # Check if analyzed_command_result exists
        if hasattr(result, "analyzed_command_result") and result.analyzed_command_result is not None:
            logger.info("Graph execution successful, analyzed_command_result is available")
            # Return the response
            return AnalyzeResponse(
                analyzed_command_result=result.analyzed_command_result
            )
        else:
            logger.error("Graph execution completed but analyzed_command_result is not available")
            logger.info(f"Result object attributes: {dir(result)}")
            logger.info(f"Result object type: {type(result)}")
            
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
    
    # settings モジュールの値をデバッグログに出力
    from wish_models import settings
    logger.info("Settings values:")
    logger.info(f"settings.OPENAI_API_KEY exists: {bool(settings.OPENAI_API_KEY)}")
    logger.info(f"settings.OPENAI_API_KEY length: {len(settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else 0}")
    logger.info(f"settings.OPENAI_MODEL: {settings.OPENAI_MODEL}")
    logger.info(f"settings.LANGCHAIN_API_KEY exists: {bool(settings.LANGCHAIN_API_KEY)}")
    logger.info(f"settings.LANGCHAIN_API_KEY length: {len(settings.LANGCHAIN_API_KEY) if settings.LANGCHAIN_API_KEY else 0}")
    logger.info(f"settings.LANGCHAIN_TRACING_V2: {settings.LANGCHAIN_TRACING_V2}")
    logger.info(f"settings.LANGCHAIN_ENDPOINT: {settings.LANGCHAIN_ENDPOINT}")
    logger.info(f"settings.LANGCHAIN_PROJECT: {settings.LANGCHAIN_PROJECT}")
    
    # 環境変数の読み込み元ファイルを確認
    wish_home = settings.WISH_HOME
    wish_home_env = os.path.join(wish_home, "env")
    logger.info(f"WISH_HOME: {wish_home}")
    logger.info(f"Checking if env file exists at {wish_home_env}: {os.path.exists(wish_home_env)}")

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
