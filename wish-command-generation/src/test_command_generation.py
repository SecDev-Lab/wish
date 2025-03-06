"""Test script for the command generation system."""

from wish_command_generation import create_command_generation_graph
from wish_command_generation.models import GraphState
from wish_models.wish.wish import Wish


def main():
    """Main function"""
    # Create the graph
    graph = create_command_generation_graph()

    # Prepare the input
    wish = Wish.create(wish="Conduct a full port scan on IP 10.10.10.123.")

    # Execute the graph
    initial_state = GraphState(wish=wish)
    result = graph.invoke(initial_state)

    # Display the results
    print("Generated commands:")
    for i, cmd in enumerate(result["command_inputs"], 1):
        print(f"{i}. Command: {cmd.command}")
        print(f"   Timeout: {cmd.timeout_sec + "seconds" if cmd.timeout_sec else "None"}")
        print()


if __name__ == "__main__":
    main()
