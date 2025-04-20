"""Command generator for wish-command-generation."""

import logging
from typing import List

from wish_models import Wish
from wish_models.command_result import CommandInput
from wish_models.system_info import SystemInfo

from .exceptions import CommandGenerationError
from .graph import create_command_generation_graph


class CommandGenerator:
    """Generates commands based on a wish."""

    def generate_commands(self, wish: Wish, system_info: SystemInfo = None) -> List[CommandInput]:
        """Generate commands based on a wish.

        Args:
            wish: The wish to generate commands for.
            system_info: Optional system information to inform command generation.

        Returns:
            A list of CommandInput objects.

        Raises:
            Exception: If there is an error generating commands.
        """
        # Create the command generation graph
        graph = create_command_generation_graph()

        # Execute the graph with system info if available
        state_input = {"wish": wish}
        if system_info:
            state_input["system_info"] = system_info

        try:
            result = graph.invoke(state_input, {"run_name": "ActL1-Command-Generation"})

            # Return the generated commands
            return result["command_inputs"]
        except Exception as e:
            # Log the error
            logging.error(f"Error in command generation graph: {str(e)}")

            # Re-raise as CommandGenerationError if it's not already
            if not isinstance(e, CommandGenerationError):
                raise CommandGenerationError(f"Command generation failed: {str(e)}") from e
            raise
