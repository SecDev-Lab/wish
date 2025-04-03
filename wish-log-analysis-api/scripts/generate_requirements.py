#!/usr/bin/env python3
"""
Generate requirements.txt from pyproject.toml dependencies.
This script extracts production dependencies from pyproject.toml
and writes them to requirements.txt in the project root.

For SAM deployment:
- Replaces local wish-* references with PyPI versions
- Uses latest versions for all wish-* packages
"""

import re
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

        # Process dependencies for SAM deployment
        processed_deps = []
        for dep in deps:
            # Check if this is a local wish-* reference (e.g. ../wish-models)
            if dep.startswith("../wish-"):
                # Extract package name from path and use latest version
                package_name = dep.split("/")[-1]
                processed_deps.append(package_name)
            # Check if this is a wish-* package with version constraint
            elif dep.startswith("wish-"):
                # Extract just the package name without version constraints
                package_name = re.split(r'[<>=~]', dep)[0].strip()
                processed_deps.append(package_name)
            else:
                # Keep other dependencies as they are
                processed_deps.append(dep)

        # Write dependencies to requirements.txt in project root
        requirements_path = Path("requirements.txt")
        with open(requirements_path, "w") as f:
            for dep in processed_deps:
                f.write(f"{dep}\n")

        print(f"Generated requirements.txt with {len(processed_deps)} dependencies")
        return True

    except Exception as e:
        print(f"Error generating requirements.txt: {e}", file=sys.stderr)
        return False


if __name__ == "__main__":
    success = extract_dependencies()
    sys.exit(0 if success else 1)
