"""
Testing framework for wish tools.

This module provides utilities for testing tool implementations,
including test case definitions, validators, and reporting.
"""

import asyncio
import tempfile
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from .base import BaseTool, ToolContext, ToolResult


@dataclass
class TestCase:
    """Test case for a tool."""

    name: str
    description: str
    capability: str
    parameters: Dict[str, Any]
    expected_success: bool
    validators: List[Callable[[ToolResult], tuple[bool, str]]]
    timeout: int = 300
    skip_if: Optional[Callable[[], bool]] = None


@dataclass
class TestResult:
    """Result of a test case."""

    test_case: TestCase
    passed: bool
    execution_time: float
    tool_result: Optional[ToolResult]
    error: Optional[str]
    validation_errors: List[str]


class OutputValidator:
    """Validator for tool output."""

    def __init__(self, contains: Optional[str] = None, not_contains: Optional[str] = None):
        self.contains = contains
        self.not_contains = not_contains

    def __call__(self, result: ToolResult) -> tuple[bool, str]:
        if self.contains and self.contains not in result.output:
            return False, f"Output should contain '{self.contains}'"

        if self.not_contains and self.not_contains in result.output:
            return False, f"Output should not contain '{self.not_contains}'"

        return True, ""


class ExitCodeValidator:
    """Validator for exit codes."""

    def __init__(self, expected: int):
        self.expected = expected

    def __call__(self, result: ToolResult) -> tuple[bool, str]:
        if result.exit_code != self.expected:
            return False, f"Expected exit code {self.expected}, got {result.exit_code}"
        return True, ""


class MetadataValidator:
    """Validator for metadata content."""

    def __init__(self, required_keys: List[str]):
        self.required_keys = required_keys

    def __call__(self, result: ToolResult) -> tuple[bool, str]:
        for key in self.required_keys:
            if key not in result.metadata:
                return False, f"Metadata missing required key: {key}"
        return True, ""


class PerformanceValidator:
    """Validator for performance requirements."""

    def __init__(self, max_time: float):
        self.max_time = max_time

    def __call__(self, result: ToolResult) -> tuple[bool, str]:
        if result.execution_time > self.max_time:
            return False, f"Execution took {result.execution_time:.2f}s, max allowed {self.max_time}s"
        return True, ""


class ToolTester:
    """Framework for testing tools."""

    def __init__(self, tool: BaseTool, context: Optional[ToolContext] = None):
        self.tool = tool
        self.context = context or self._default_context()

    def _default_context(self) -> ToolContext:
        """Create default test context."""
        temp_dir = tempfile.mkdtemp()
        return ToolContext(working_directory=temp_dir, environment_variables={}, run_id="test-run")

    async def test_availability(self) -> TestResult:
        """Test if tool is available."""
        test_case = TestCase(
            name="availability_check",
            description="Check if tool is available on the system",
            capability="",
            parameters={},
            expected_success=True,
            validators=[],
        )

        start_time = time.time()
        try:
            is_available, error = await self.tool.validate_availability()

            return TestResult(
                test_case=test_case,
                passed=is_available,
                execution_time=time.time() - start_time,
                tool_result=None,
                error=error,
                validation_errors=[],
            )
        except Exception as e:
            return TestResult(
                test_case=test_case,
                passed=False,
                execution_time=time.time() - start_time,
                tool_result=None,
                error=str(e),
                validation_errors=[],
            )

    async def run_test_case(self, test_case: TestCase) -> TestResult:
        """Run a single test case."""
        # Check skip condition
        if test_case.skip_if and test_case.skip_if():
            return TestResult(
                test_case=test_case,
                passed=True,
                execution_time=0,
                tool_result=None,
                error="Test skipped",
                validation_errors=[],
            )

        start_time = time.time()
        validation_errors = []

        try:
            # Generate command
            command = self.tool.generate_command(
                capability=test_case.capability, parameters=test_case.parameters, context=self.context
            )

            # Execute command
            tool_result = await asyncio.wait_for(self.tool.execute(command, self.context), timeout=test_case.timeout)

            # Check basic success/failure
            if tool_result.success != test_case.expected_success:
                validation_errors.append(
                    f"Expected success={test_case.expected_success}, got success={tool_result.success}"
                )

            # Run validators
            for validator in test_case.validators:
                is_valid, error = validator(tool_result)
                if not is_valid:
                    validation_errors.append(error)

            passed = len(validation_errors) == 0

            return TestResult(
                test_case=test_case,
                passed=passed,
                execution_time=time.time() - start_time,
                tool_result=tool_result,
                error=None,
                validation_errors=validation_errors,
            )

        except asyncio.TimeoutError:
            return TestResult(
                test_case=test_case,
                passed=False,
                execution_time=test_case.timeout,
                tool_result=None,
                error="Test timed out",
                validation_errors=validation_errors,
            )
        except Exception as e:
            return TestResult(
                test_case=test_case,
                passed=False,
                execution_time=time.time() - start_time,
                tool_result=None,
                error=str(e),
                validation_errors=validation_errors,
            )

    async def run_test_suite(self, test_cases: List[TestCase]) -> List[TestResult]:
        """Run a suite of test cases."""
        results = []

        # First check availability
        availability_result = await self.test_availability()
        results.append(availability_result)

        if not availability_result.passed:
            # Skip other tests if tool not available
            return results

        # Run test cases
        for test_case in test_cases:
            result = await self.run_test_case(test_case)
            results.append(result)

        return results

    def generate_report(self, results: List[TestResult]) -> str:
        """Generate test report."""
        report_lines = [
            f"# Test Report for {self.tool.metadata.name}",
            f"\nTool Version: {self.tool.metadata.version}",
            f"Total Tests: {len(results)}",
            f"Passed: {sum(1 for r in results if r.passed)}",
            f"Failed: {sum(1 for r in results if not r.passed)}",
            "\n## Test Results\n",
        ]

        for result in results:
            status = "✅ PASSED" if result.passed else "❌ FAILED"
            report_lines.append(f"### {result.test_case.name} - {status}")
            report_lines.append(f"**Description:** {result.test_case.description}")
            report_lines.append(f"**Execution Time:** {result.execution_time:.2f}s")

            if result.error:
                report_lines.append(f"**Error:** {result.error}")

            if result.validation_errors:
                report_lines.append("**Validation Errors:**")
                for error in result.validation_errors:
                    report_lines.append(f"- {error}")

            if result.tool_result:
                report_lines.append("\n**Tool Output Preview:**")
                output_preview = result.tool_result.output[:500]
                if len(result.tool_result.output) > 500:
                    output_preview += "... (truncated)"
                report_lines.append(f"```\n{output_preview}\n```")

            report_lines.append("")

        return "\n".join(report_lines)


def create_basic_test_suite(tool_name: str) -> List[TestCase]:
    """Create a basic test suite for any tool."""
    return [
        TestCase(
            name="metadata_check",
            description="Verify tool metadata is properly configured",
            capability="",
            parameters={},
            expected_success=True,
            validators=[],
        )
    ]
