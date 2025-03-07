"""Test script for the command generation system."""

from wish_models.wish.wish import Wish

from wish_command_generation import CommandGenerator


def main():
    """Main function"""
    # Create the command generator
    command_generator = CommandGenerator()

    # Prepare the input
    wish = Wish.create(wish="Conduct a full port scan on IP 10.10.10.123.")

    # Generate commands
    command_inputs = command_generator.generate_commands(wish)

    # Display the results
    print("Generated commands:")
    for i, cmd in enumerate(command_inputs, 1):
        print(f"{i}. Command: {cmd.command}")
        print(f"   Timeout: {f'{cmd.timeout_sec} seconds' if cmd.timeout_sec else 'None'}")
        print()


if __name__ == "__main__":
    main()
