#!/usr/bin/env python3
"""
Generate requirements.txt from pyproject.toml dependencies.
This script extracts production dependencies from pyproject.toml
and writes them to requirements.txt.
"""

import tomli
import sys
from pathlib import Path


def extract_dependencies():
    """Extract dependencies from pyproject.toml and write to requirements.txt."""
    try:
        with open("pyproject.toml", "rb") as f:
            data = tomli.load(f)
        
        # Extract production dependencies
        deps = data["project"]["dependencies"]
        
        with open("requirements.txt", "w") as f:
            for dep in deps:
                f.write(f"{dep}\n")
            
            # Add wish-models as editable install if it's in uv.sources
            if "tool" in data and "uv" in data["tool"] and "sources" in data["tool"]["uv"]:
                sources = data["tool"]["uv"]["sources"]
                if "wish-models" in sources and "path" in sources["wish-models"]:
                    path = sources["wish-models"]["path"]
                    f.write(f"-e {path}\n")
        
        print(f"Generated requirements.txt with {len(deps)} dependencies")
        return True
    
    except Exception as e:
        print(f"Error generating requirements.txt: {e}", file=sys.stderr)
        return False


if __name__ == "__main__":
    success = extract_dependencies()
    sys.exit(0 if success else 1)
