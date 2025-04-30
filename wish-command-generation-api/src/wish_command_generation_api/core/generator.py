"""Generator module for the command generation API."""

import logging
from typing import Optional

from wish_models.command_result import CommandInput
from wish_models.settings import Settings

from ..config import GeneratorConfig
from ..graph import create_command_generation_graph
from ..models import GeneratedCommand, GenerateRequest, GenerateResponse, GraphState

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def generate_commands(
    request: GenerateRequest,
    settings_obj: Settings,
    config: Optional[GeneratorConfig] = None
) -> GenerateResponse:
    """Generate commands using the command generation graph.

    Args:
        request: The request containing the query and context for command generation.
        config: Configuration object (if None, load from environment variables)

    Returns:
        The response containing the generated commands.
    """
    try:
        # Create the graph
        graph = create_command_generation_graph(config=config, settings_obj=settings_obj)

        # Create the initial state
        initial_state = GraphState(
            query=request.query,
            context=request.context,
            act_result=request.act_result,
            run_id=request.run_id,
            initial_timeout_sec=request.initial_timeout_sec
        )

        # Log feedback if present
        if request.act_result:
            logger.info(f"Received feedback with {len(request.act_result)} results")
            for i, result in enumerate(request.act_result):
                logger.info(f"Feedback {i+1}: Command '{result.command}' - State: {result.state}")

        # Run the graph with static name
        result = graph.invoke(initial_state, {"run_name": "ActL1-Command-Generation"})

        # Extract the generated commands
        generated_commands = None

        # Method 1: Access as attribute
        if hasattr(result, "generated_commands") and result.generated_commands is not None:
            generated_commands = result.generated_commands

        # Method 2: Access as dictionary
        elif isinstance(result, dict) and "generated_commands" in result:
            generated_commands = result["generated_commands"]

        # Method 3: Check for AddableValuesDict structure
        elif (hasattr(result, "values")
              and isinstance(result.values, dict)
              and "generated_commands" in result.values):
            generated_commands = result.values["generated_commands"]

        # Method 4: Get result from the last node
        elif hasattr(result, "result_formatter") and result.result_formatter is not None:
            if hasattr(result.result_formatter, "generated_commands"):
                generated_commands = result.result_formatter.generated_commands

        assert generated_commands is not None, "No generated commands found in the result"

        # 各コマンドのタイムアウト値が設定されていることを確認
        for cmd in generated_commands:
            if cmd.timeout_sec is None:
                logger.warning(f"Command has no timeout specified: {cmd.command}")
                # エラーを発生させる（タイムアウト値が必須）
                raise ValueError(f"Command has no timeout specified: {cmd.command}")

        return GenerateResponse(
            generated_commands=generated_commands
        )
    except Exception as e:
        raise RuntimeError("Error generating commands") from e
