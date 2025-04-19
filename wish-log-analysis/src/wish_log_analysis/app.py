import json
import logging
import traceback
from typing import Any, Dict, Optional

import requests
from wish_models.command_result import CommandResult
from wish_models.command_result.command_state import CommandState
from wish_models.settings import Settings

from .models import LogAnalysisOutput

logger = logging.getLogger(__name__)


class LogAnalysisClient:
    """
    Log Analysis API Client
    """
    def __init__(self, api_url: Optional[str] = None):
        if api_url:
            self.api_url = api_url
        else:
            settings_obj = Settings()
            self.api_url = f"{settings_obj.WISH_API_BASE_URL}/analyze"

    def analyze(self, command_result: CommandResult) -> LogAnalysisOutput:
        """
        Call the API server to perform analysis and return LogAnalysisOutput

        Args:
            command_result: Command execution result to be analyzed

        Returns:
            LogAnalysisOutput: Analysis result
        """
        # Send API request
        try:
            print(f"API request destination: {self.api_url}")
            request_data = {"command_result": command_result.model_dump()}
            print(f"Request data: {json.dumps(request_data, indent=2)}")

            response = requests.post(
                self.api_url,
                json=request_data,
                headers={"Content-Type": "application/json"},
                timeout=30,
            )
            print(f"Response status: {response.status_code}")

            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                print(f"HTTP error: {e}")
                print(f"Response content: {response.text}")
                raise

            # Parse response
            result = response.json()

            # Process server response appropriately
            if "analyzed_command_result" in result:
                analyzed_result = result["analyzed_command_result"]
                return LogAnalysisOutput(
                    summary=analyzed_result.get("log_summary") or "No analysis results",
                    state=analyzed_result.get("state", "OTHERS"),
                    error_message=result.get("error")
                )
            else:
                return LogAnalysisOutput(
                    summary="Invalid API response format",
                    state="error",
                    error_message="Invalid API response format"
                )

        except requests.RequestException as e:
            logger.error(f"API request failed: {e}")
            # Fallback processing for errors
            return LogAnalysisOutput(
                summary="API request failed",
                state="error",
                error_message=str(e),
            )

    def analyze_result(self, command_result: CommandResult) -> CommandResult:
        """
        Call the API server to perform analysis and return CommandResult

        Args:
            command_result: Command execution result to be analyzed

        Returns:
            CommandResult: Analyzed CommandResult
        """
        try:
            # Send API request and analyze
            output = self.analyze(command_result)

            # Convert state string to CommandState enum
            try:
                command_state = (CommandState[output.state]
                                if output.state in CommandState.__members__
                                else CommandState.API_ERROR)
            except (KeyError, ValueError):
                command_state = CommandState.API_ERROR

            # Create new CommandResult
            analyzed_result = CommandResult(
                num=command_result.num,
                command=command_result.command,
                exit_code=command_result.exit_code,
                log_files=command_result.log_files,
                log_summary=output.summary,
                state=command_state,
                created_at=command_result.created_at,
                finished_at=command_result.finished_at
            )

            return analyzed_result

        except Exception as e:
            # Fallback processing for errors
            logger.error(f"Error analyzing command result: {str(e)}")
            logger.error(traceback.format_exc())

            # Return CommandResult with error information
            error_result = CommandResult(
                num=command_result.num,
                command=command_result.command,
                exit_code=command_result.exit_code,
                log_files=command_result.log_files,
                log_summary=f"Error analyzing command: {str(e)}",
                state=CommandState.API_ERROR,
                created_at=command_result.created_at,
                finished_at=command_result.finished_at
            )

            return error_result


def analyze_logs(command_result: CommandResult) -> LogAnalysisOutput:
    """
    Call the API server to perform analysis and return LogAnalysisOutput

    Args:
        command_result: Command execution result to be analyzed

    Returns:
        LogAnalysisOutput: Analysis result
    """
    client = LogAnalysisClient()
    return client.analyze(command_result)


def analyze_result(command_result: CommandResult) -> CommandResult:
    """
    Call the API server to perform analysis and return CommandResult

    Args:
        command_result: Command execution result to be analyzed

    Returns:
        CommandResult: Analyzed CommandResult
    """
    client = LogAnalysisClient()
    return client.analyze_result(command_result)


def lambda_handler(event: Dict[str, Any], context: Optional[Any] = None) -> Dict[str, Any]:
    """
    AWS Lambda handler
    """
    logger.info("Received event: %s", json.dumps(event))

    try:
        # Process events from APIGateway
        if "body" in event:
            body = json.loads(event["body"])
            command_result = CommandResult(
                num=1,
                command=body.get("command", ""),
                state=body.get("state", "DOING"),
                exit_code=body.get("exit_code", 0),
                log_files={"stdout": body.get("output", ""), "stderr": ""},
                created_at=body.get("created_at", None),
            )
        else:
            # For direct invocation
            command_result = CommandResult(
                num=1,
                command=event.get("command", ""),
                state=event.get("state", "DOING"),
                exit_code=event.get("exit_code", 0),
                log_files={"stdout": event.get("output", ""), "stderr": ""},
                created_at=event.get("created_at", None),
            )

        # Execute analysis
        result = analyze_logs(command_result)

        # Return response
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps(result.model_dump())
        }

    except Exception as e:
        logger.exception("Error processing request")
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "error": str(e)
            })
        }
