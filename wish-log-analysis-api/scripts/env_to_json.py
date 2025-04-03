#!/usr/bin/env python
"""Convert ~/.wish/env file to SAM CLI compatible JSON format."""

import json
import os


def parse_env_file(file_path):
    """Parse an environment file and return a dictionary of key-value pairs."""
    if not os.path.exists(file_path):
        print(f"Warning: Environment file {file_path} does not exist")
        return {}

    env_vars = {}
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            if '=' in line:
                key, value = line.split('=', 1)
                env_vars[key] = value

    return env_vars

def main():
    """Convert ~/.wish/env to SAM CLI compatible JSON format."""
    # Get WISH_HOME from environment or use default
    wish_home = os.environ.get("WISH_HOME", os.path.expanduser("~/.wish"))
    env_file = os.path.join(wish_home, "env")

    # Parse the env file
    env_vars = parse_env_file(env_file)

    # Create SAM CLI compatible JSON structure
    sam_env = {
        "AnalyzeFunction": env_vars
    }

    # Write to .env.json file
    output_file = ".env.json"
    with open(output_file, 'w') as f:
        json.dump(sam_env, f, indent=2)

    print(f"Environment variables from {env_file} written to {output_file}")

if __name__ == "__main__":
    main()
