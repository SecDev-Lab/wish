#!/usr/bin/env python3
"""
Generate requirements.txt from pyproject.toml dependencies.
This script extracts production dependencies from pyproject.toml
and writes them to requirements.txt in the project root.
"""

import sys
from pathlib import Path

import tomli


def extract_dependencies():
    """Extract dependencies from pyproject.toml and write to requirements.txt in project root."""
    try:
        with open("pyproject.toml", "rb") as f:
            data = tomli.load(f)

        # Extract production dependencies
        deps = data["project"]["dependencies"]

        # Write dependencies to requirements.txt in project root
        requirements_path = Path("requirements.txt")
        with open(requirements_path, "w") as f:
            for dep in deps:
                f.write(f"{dep}\n")

        print(f"Generated requirements.txt with {len(deps)} dependencies")
        return True

    except Exception as e:
        print(f"Error generating requirements.txt: {e}", file=sys.stderr)
        return False


if __name__ == "__main__":
    success = extract_dependencies()
    sys.exit(0 if success else 1)
