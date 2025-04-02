#!/usr/bin/env python3
"""
Generate requirements.txt from pyproject.toml dependencies.
This script extracts production dependencies from pyproject.toml
and writes them to vendor/requirements.txt.
"""

import tomli
import sys
from pathlib import Path


def extract_dependencies():
    """Extract dependencies from pyproject.toml and write to vendor/requirements.txt."""
    try:
        with open("pyproject.toml", "rb") as f:
            data = tomli.load(f)
        
        # Extract production dependencies
        deps = data["project"]["dependencies"]
        
        # Create vendor directory if it doesn't exist
        vendor_dir = Path("vendor")
        vendor_dir.mkdir(exist_ok=True)
        
        # Write dependencies to vendor/requirements.txt
        requirements_path = vendor_dir / "requirements.txt"
        with open(requirements_path, "w") as f:
            for dep in deps:
                f.write(f"{dep}\n")
        
        print(f"Generated vendor/requirements.txt with {len(deps)} dependencies")
        return True
    
    except Exception as e:
        print(f"Error generating vendor/requirements.txt: {e}", file=sys.stderr)
        return False


if __name__ == "__main__":
    success = extract_dependencies()
    sys.exit(0 if success else 1)
