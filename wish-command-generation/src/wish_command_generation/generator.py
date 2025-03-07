"""Command generator for wish-command-generation."""

from typing import List

from wish_models import Wish
from wish_models.command_result import CommandInput

from .graph import create_command_generation_graph


class CommandGenerator:
    """Generates commands based on a wish."""

    def generate_commands(self, wish: Wish) -> List[CommandInput]:
        """Generate commands based on a wish.

        Args:
            wish: The wish to generate commands for.

        Returns:
            A list of CommandInput objects.
        """
        # Create the command generation graph
        graph = create_command_generation_graph()

        # Execute the graph
        result = graph.invoke({"wish": wish})

        # Return the generated commands
        return result["command_inputs"]
