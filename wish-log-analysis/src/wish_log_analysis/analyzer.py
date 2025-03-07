"""Log analyzer for wish-log-analysis."""

from typing import Optional

from wish_models.command_result import CommandResult

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
        # Create the log analysis graph
        graph = create_log_analysis_graph()

        # Execute the graph
        result = graph.invoke({"command_result": command_result})

        # Return the analyzed command result
        return result["analyzed_command_result"]
