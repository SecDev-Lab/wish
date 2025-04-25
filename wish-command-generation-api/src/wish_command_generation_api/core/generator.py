"""Generator module for the command generation API."""

import logging
from typing import Optional

from wish_models.settings import Settings

from ..config import GeneratorConfig
from ..graph import create_command_generation_graph
from ..models import GeneratedCommand, GenerateRequest, GenerateResponse, GraphState

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def generate_command(
    request: GenerateRequest,
    settings_obj: Settings,
    config: Optional[GeneratorConfig] = None
) -> GenerateResponse:
    """Generate a command using the command generation graph.

    Args:
        request: The request containing the query and context for command generation.
        config: Configuration object (if None, load from environment variables)

    Returns:
        The response containing the generated command.
    """
    try:
        # Create the graph
        graph = create_command_generation_graph(config=config, settings_obj=settings_obj)

        # Create the initial state
        initial_state = GraphState(
            query=request.query,
            context=request.context,
            act_result=request.act_result,
            run_id=request.run_id
        )

        # Log feedback if present
        if request.act_result:
            logger.info(f"Received feedback with {len(request.act_result)} results")
            for i, result in enumerate(request.act_result):
                logger.info(f"Feedback {i+1}: Command '{result.command}' - State: {result.state}")

        # Run the graph with static name
        result = graph.invoke(initial_state, {"run_name": "ActL1-Command-Generation"})

        # Extract the generated command
        generated_command = None

        # Method 1: Access as attribute
        if hasattr(result, "generated_command") and result.generated_command is not None:
            generated_command = result.generated_command

        # Method 2: Access as dictionary
        elif isinstance(result, dict) and "generated_command" in result:
            generated_command = result["generated_command"]

        # Method 3: Check for AddableValuesDict structure
        elif (hasattr(result, "values")
              and isinstance(result.values, dict)
              and "generated_command" in result.values):
            generated_command = result.values["generated_command"]

        # Method 4: Get result from the last node
        elif hasattr(result, "result_formatter") and result.result_formatter is not None:
            if hasattr(result.result_formatter, "generated_command"):
                generated_command = result.result_formatter.generated_command

        # If result was found
        if generated_command is not None:
            return GenerateResponse(
                generated_command=generated_command
            )

        # Fallback: If result was not found
        logger.error("Could not find generated_command in any expected location")

        # Create a fallback generated_command
        fallback_command = GeneratedCommand(
            command="echo 'Command generation failed'",
            explanation="Error: Failed to generate command due to API error"
        )

        return GenerateResponse(
            generated_command=fallback_command,
            error="Failed to generate command"
        )
    except Exception as e:
        logger.exception("Error generating command")

        # Create a fallback generated_command for the exception case
        fallback_command = GeneratedCommand(
            command="echo 'Command generation failed'",
            explanation=f"Error: {str(e)}"
        )

        return GenerateResponse(
            generated_command=fallback_command,
            error=str(e)
        )
