#!/usr/bin/env python
"""Run tests for the wish-command-generation-api package."""

import argparse
import os
import subprocess
import sys


def run_command(command):
    """Run a shell command and return the exit code."""
    print(f"Running: {' '.join(command)}")
    result = subprocess.run(command)
    return result.returncode


def run_tests(test_type=None, verbose=False):
    """Run tests based on the specified type.

    Args:
        test_type: Type of tests to run (unit, integration, all)
        verbose: Whether to run tests in verbose mode
    """
    pytest_args = ["uv", "run", "pytest"]
    
    if verbose:
        pytest_args.append("-v")

    if test_type == "unit":
        pytest_args.append("tests/unit")
    elif test_type == "integration":
        pytest_args.append("tests/integration")
        pytest_args.append("-m")
        pytest_args.append("integration")
    # If no type specified or "all", run all tests

    return run_command(pytest_args)


def main():
    """Parse arguments and run tests."""
    parser = argparse.ArgumentParser(description="Run tests for wish-command-generation-api")
    parser.add_argument(
        "--type",
        choices=["unit", "integration", "all"],
        default="all",
        help="Type of tests to run (default: all)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Run tests in verbose mode",
    )
    
    args = parser.parse_args()
    
    # Run tests
    exit_code = run_tests(args.type, args.verbose)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
