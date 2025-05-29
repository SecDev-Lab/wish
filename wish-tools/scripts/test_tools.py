#!/usr/bin/env python3
"""
Tool testing script for wish-tools.

This script runs comprehensive tests on all available tools
and generates detailed reports about their functionality.
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from wish_tools.framework.registry import tool_registry
from wish_tools.framework.testing import (
    ExitCodeValidator,
    OutputValidator,
    PerformanceValidator,
    TestCase,
    ToolTester,
)


def create_bash_test_suite() -> List[TestCase]:
    """Create test suite for BashTool."""
    return [
        TestCase(
            name="simple_echo",
            description="Test simple echo command",
            capability="execute",
            parameters={"command": "echo 'Hello World'"},
            expected_success=True,
            validators=[
                OutputValidator(contains="Hello World"),
                ExitCodeValidator(expected=0),
                PerformanceValidator(max_time=5.0),
            ],
        ),
        TestCase(
            name="file_listing",
            description="Test file listing command",
            capability="execute",
            parameters={"command": "ls -la"},
            expected_success=True,
            validators=[ExitCodeValidator(expected=0), PerformanceValidator(max_time=10.0)],
        ),
        TestCase(
            name="invalid_command",
            description="Test handling of invalid command",
            capability="execute",
            parameters={"command": "nonexistentcommand12345"},
            expected_success=False,
            validators=[
                ExitCodeValidator(expected=127)  # Command not found
            ],
        ),
        TestCase(
            name="script_execution",
            description="Test script execution capability",
            capability="script",
            parameters={"script": "#!/bin/bash\necho 'Script output'\ndate +%Y", "args": ""},
            expected_success=True,
            validators=[OutputValidator(contains="Script output"), ExitCodeValidator(expected=0)],
        ),
    ]


def create_msfconsole_test_suite() -> List[TestCase]:
    """Create test suite for MsfconsoleTool."""

    def skip_if_no_msfconsole():
        """Skip test if msfconsole is not available."""
        import subprocess

        try:
            subprocess.run(["msfconsole", "-v"], capture_output=True, timeout=10)
            return False
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return True

    return [
        TestCase(
            name="module_search",
            description="Test module search functionality",
            capability="search",
            parameters={"query": "smb", "type": "auxiliary"},
            expected_success=True,
            validators=[OutputValidator(contains="auxiliary"), ExitCodeValidator(expected=0)],
            skip_if=skip_if_no_msfconsole,
        ),
        TestCase(
            name="module_info",
            description="Test module info retrieval",
            capability="info",
            parameters={"module": "auxiliary/scanner/smb/smb_version"},
            expected_success=True,
            validators=[OutputValidator(contains="Name:"), ExitCodeValidator(expected=0)],
            skip_if=skip_if_no_msfconsole,
        ),
    ]


# NmapTool removed - using bash for nmap commands instead


async def test_single_tool(tool_name: str, test_cases: List[TestCase]) -> Dict[str, Any]:
    """Test a single tool with the provided test cases."""
    print(f"\n{'=' * 60}")
    print(f"Testing tool: {tool_name}")
    print(f"{'=' * 60}")

    try:
        tool = tool_registry.get_tool(tool_name)
        tester = ToolTester(tool)

        # Run test suite
        results = await tester.run_test_suite(test_cases)

        # Generate and print report
        report = tester.generate_report(results)
        print(report)

        # Return summary
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.passed)

        return {
            "tool_name": tool_name,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "success_rate": passed_tests / total_tests if total_tests > 0 else 0,
            "results": results,
        }

    except Exception as e:
        print(f"Error testing {tool_name}: {e}")
        return {"tool_name": tool_name, "total_tests": 0, "passed_tests": 0, "success_rate": 0, "error": str(e)}


async def test_all_tools() -> List[Dict[str, Any]]:
    """Test all available tools."""
    # Define test suites for each tool
    test_suites = {"bash": create_bash_test_suite(), "msfconsole": create_msfconsole_test_suite()}

    results = []

    for tool_name, test_cases in test_suites.items():
        if tool_registry.has_tool(tool_name):
            result = await test_single_tool(tool_name, test_cases)
            results.append(result)
        else:
            print(f"\nTool {tool_name} not available, skipping tests")
            results.append(
                {
                    "tool_name": tool_name,
                    "total_tests": 0,
                    "passed_tests": 0,
                    "success_rate": 0,
                    "error": "Tool not available",
                }
            )

    return results


def print_summary(results: List[Dict[str, Any]]):
    """Print a summary of all test results."""
    print(f"\n{'=' * 60}")
    print("TEST SUMMARY")
    print(f"{'=' * 60}")

    total_tools = len(results)
    total_tests = sum(r["total_tests"] for r in results)
    total_passed = sum(r["passed_tests"] for r in results)

    print(f"Tools tested: {total_tools}")
    print(f"Total tests: {total_tests}")
    print(f"Tests passed: {total_passed}")
    print(f"Overall success rate: {total_passed / total_tests * 100:.1f}%" if total_tests > 0 else "N/A")
    print()

    # Per-tool summary
    print("Per-tool results:")
    print("-" * 60)
    print(f"{'Tool':<15} {'Tests':<8} {'Passed':<8} {'Success Rate':<12} {'Status'}")
    print("-" * 60)

    for result in results:
        status = "✅ PASS" if result["success_rate"] == 1.0 and result["total_tests"] > 0 else "❌ FAIL"
        if result["total_tests"] == 0:
            status = "⚠️  SKIP"

        success_rate = f"{result['success_rate'] * 100:.1f}%" if result["total_tests"] > 0 else "N/A"

        print(
            f"{result['tool_name']:<15} {result['total_tests']:<8} "
            f"{result['passed_tests']:<8} {success_rate:<12} {status}"
        )


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Test wish-tools framework")
    parser.add_argument("--tool", type=str, help="Test only the specified tool")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).parent.parent / "test-reports",
        help="Directory to save test reports",
    )
    parser.add_argument("--save-reports", action="store_true", help="Save detailed test reports to files")

    args = parser.parse_args()

    print("Wish Tools Testing Framework")
    print("=" * 60)

    # Auto-discover tools
    try:
        tool_registry.auto_discover_tools("wish_tools.tools")
        discovered_tools = tool_registry.get_tool_names()
        print(f"Discovered tools: {', '.join(discovered_tools)}")
    except Exception as e:
        print(f"Warning: Tool auto-discovery failed: {e}")
        discovered_tools = []

    if not discovered_tools:
        print("No tools discovered. Exiting.")
        return

    # Run tests
    if args.tool:
        if not tool_registry.has_tool(args.tool):
            print(f"Tool '{args.tool}' not found")
            return

        # Test single tool
        test_suites = {"bash": create_bash_test_suite(), "msfconsole": create_msfconsole_test_suite()}

        if args.tool in test_suites:
            results = [await test_single_tool(args.tool, test_suites[args.tool])]
        else:
            print(f"No test suite defined for tool '{args.tool}'")
            return
    else:
        # Test all tools
        results = await test_all_tools()

    # Print summary
    print_summary(results)

    # Save reports if requested
    if args.save_reports:
        args.output_dir.mkdir(parents=True, exist_ok=True)

        for result in results:
            if "results" in result:
                tool_name = result["tool_name"]
                report_file = args.output_dir / f"{tool_name}-test-report.md"

                # Get tool and regenerate detailed report
                try:
                    tool = tool_registry.get_tool(tool_name)
                    tester = ToolTester(tool)
                    detailed_report = tester.generate_report(result["results"])

                    with open(report_file, "w") as f:
                        f.write(detailed_report)

                    print(f"Saved detailed report: {report_file}")
                except Exception as e:
                    print(f"Error saving report for {tool_name}: {e}")


if __name__ == "__main__":
    asyncio.run(main())
