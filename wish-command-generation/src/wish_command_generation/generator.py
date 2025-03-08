"""Command generator for wish-command-generation."""

from typing import List

from wish_models import Wish
from wish_models.command_result import CommandInput
from wish_models.system_info import SystemInfo

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
        """
        # Create the command generation graph
        graph = create_command_generation_graph()

        # Execute the graph with system info if available
        state_input = {"wish": wish}
        if system_info:
            state_input["system_info"] = system_info

        result = graph.invoke(state_input)

        # Return the generated commands
        return result["command_inputs"]
