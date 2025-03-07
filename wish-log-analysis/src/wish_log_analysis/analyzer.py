"""Log analyzer for wish-log-analysis."""

import logging
import traceback

from wish_models.command_result import CommandResult
from wish_models.command_result.command_state import CommandState

from .graph import create_log_analysis_graph


class LogAnalyzer:
    """Analyzes command results based on logs."""

    def analyze_result(self, command_result: CommandResult) -> CommandResult:
        """Analyze a command result.

        Args:
            command_result: The command result to analyze. May have None fields for stdout, stderr.

        Returns:
            A CommandResult object with all fields filled.
        """
        try:
            # Configure logging
            logging.basicConfig(level=logging.INFO)

            # Log the analysis attempt
            logging.info(f"Analyzing command: {command_result.command}")
            logging.info(f"Exit code: {command_result.exit_code}")

            # Create the log analysis graph
            logging.info("Creating log analysis graph (serial execution)")
            graph = create_log_analysis_graph()
            logging.info("Graph created successfully")

            # Execute the graph
            logging.info("Invoking graph with command result")
            logging.info(f"Command: {command_result.command}")
            logging.info(f"Exit code: {command_result.exit_code}")

            # Invoke the graph with the command result
            result = graph.invoke({"command_result": command_result})

            # Log the result of each node
            logging.info("Graph execution completed")
            logging.info(f"Log summary: {result.get('log_summary')}")
            logging.info(f"Command state: {result.get('command_state')}")

            # Log successful analysis
            logging.info("Command analysis completed successfully")
            logging.info(f"Analyzed result: {result.get('analyzed_command_result')}")

            # Return the analyzed command result
            return result["analyzed_command_result"]
        except Exception as e:
            # Log the error with detailed information
            error_message = f"Error analyzing command result: {str(e)}"
            logging.error(error_message)
            logging.error(f"Command: {command_result.command}")
            logging.error(f"Exit code: {command_result.exit_code}")

            # Log stack trace for debugging
            logging.error("Stack trace:")
            logging.error(traceback.format_exc())

            # For LangGraph specific errors, provide more context
            if "Can receive only one value per step" in str(e):
                logging.error("LangGraph parallel execution error. "
                              "This may be due to concurrent updates to the same state field.")
                logging.error("Check if Annotated types are properly configured in GraphState model.")

            # Create a copy of the command result with error information
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
