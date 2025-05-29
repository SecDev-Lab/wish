"""
Tests for the wish tools framework.

This module contains tests for the core framework functionality
including tool registration, discovery, and basic execution.
"""

import tempfile

import pytest

from wish_tools.framework import (
    BaseTool,
    CommandInput,
    TestCase,
    ToolCapability,
    ToolContext,
    ToolMetadata,
    ToolResult,
    ToolTester,
    tool_registry,
)
from wish_tools.framework.testing import ExitCodeValidator, OutputValidator


class MockTool(BaseTool):
    """Mock tool for testing."""

    def _build_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="mock",
            version="1.0.0",
            description="Mock tool for testing",
            author="Test Suite",
            category="testing",
            capabilities=[
                ToolCapability(
                    name="echo",
                    description="Echo input text",
                    parameters={"text": "Text to echo"},
                    examples=["echo hello world"],
                )
            ],
            requirements=["python"],
            tags=["test", "mock"],
        )

    async def validate_availability(self):
        return True, None

    async def execute(self, command: CommandInput, context: ToolContext, **kwargs):
        # Mock execution - just echo the command
        return ToolResult(
            success=True,
            output=f"Mock output: {command.command}",
            error=None,
            exit_code=0,
            execution_time=0.1,
            metadata={"mock": True},
        )

    def generate_command(self, capability: str, parameters: dict, context=None):
        if capability == "echo":
            return CommandInput(command=f"echo {parameters['text']}", timeout_sec=30)
        raise ValueError(f"Unknown capability: {capability}")


class TestToolRegistry:
    """Test tool registry functionality."""

    def test_register_tool(self):
        """Test tool registration."""
        # Clear registry for clean test
        original_tools = tool_registry._tools.copy()
        tool_registry._tools.clear()

        try:
            tool_registry.register_tool(MockTool)
            assert tool_registry.has_tool("mock")
            assert "mock" in tool_registry.get_tool_names()
        finally:
            # Restore registry
            tool_registry._tools = original_tools

    def test_get_tool(self):
        """Test getting tool instance."""
        # Register mock tool
        tool_registry.register_tool(MockTool, override=True)

        tool = tool_registry.get_tool("mock")
        assert isinstance(tool, MockTool)
        assert tool.metadata.name == "mock"

    def test_list_tools(self):
        """Test listing all tools."""
        # Register mock tool
        tool_registry.register_tool(MockTool, override=True)

        tools = tool_registry.list_tools()
        tool_names = [t.name for t in tools]
        assert "mock" in tool_names

    def test_search_tools(self):
        """Test searching tools."""
        # Register mock tool
        tool_registry.register_tool(MockTool, override=True)

        results = tool_registry.search_tools("mock")
        assert len(results) >= 1
        assert any(t.name == "mock" for t in results)

    def test_list_by_category(self):
        """Test listing tools by category."""
        # Register mock tool
        tool_registry.register_tool(MockTool, override=True)

        tools = tool_registry.list_by_category("testing")
        assert "mock" in tools

    def test_list_by_tag(self):
        """Test listing tools by tag."""
        # Register mock tool
        tool_registry.register_tool(MockTool, override=True)

        tools = tool_registry.list_by_tag("test")
        assert "mock" in tools


class TestBaseTool:
    """Test base tool functionality."""

    def test_tool_metadata(self):
        """Test tool metadata generation."""
        tool = MockTool()
        metadata = tool.metadata

        assert metadata.name == "mock"
        assert metadata.version == "1.0.0"
        assert metadata.category == "testing"
        assert len(metadata.capabilities) == 1
        assert metadata.capabilities[0].name == "echo"

    def test_get_documentation(self):
        """Test documentation generation."""
        tool = MockTool()
        docs = tool.get_documentation()

        assert "# mock" in docs
        assert "Mock tool for testing" in docs
        assert "## Capabilities" in docs
        assert "### echo" in docs

    @pytest.mark.asyncio
    async def test_validate_availability(self):
        """Test availability validation."""
        tool = MockTool()
        is_available, error = await tool.validate_availability()

        assert is_available is True
        assert error is None

    @pytest.mark.asyncio
    async def test_execute(self):
        """Test command execution."""
        tool = MockTool()

        with tempfile.TemporaryDirectory() as temp_dir:
            context = ToolContext(working_directory=temp_dir, run_id="test")

            command = CommandInput(command="test command", timeout_sec=30)
            result = await tool.execute(command, context)

            assert result.success is True
            assert "Mock output: test command" in result.output
            assert result.exit_code == 0

    def test_generate_command(self):
        """Test command generation."""
        tool = MockTool()

        command = tool.generate_command(capability="echo", parameters={"text": "hello world"})

        assert command.command == "echo hello world"
        assert command.timeout_sec == 30


class TestToolTester:
    """Test tool testing framework."""

    @pytest.mark.asyncio
    async def test_availability_test(self):
        """Test availability testing."""
        tool = MockTool()
        tester = ToolTester(tool)

        result = await tester.test_availability()
        assert result.passed is True

    @pytest.mark.asyncio
    async def test_run_test_case(self):
        """Test running a test case."""
        tool = MockTool()
        tester = ToolTester(tool)

        test_case = TestCase(
            name="echo_test",
            description="Test echo functionality",
            capability="echo",
            parameters={"text": "hello"},
            expected_success=True,
            validators=[OutputValidator(contains="Mock output"), ExitCodeValidator(expected=0)],
        )

        result = await tester.run_test_case(test_case)
        assert result.passed is True
        assert result.tool_result is not None
        assert result.tool_result.success is True

    def test_generate_report(self):
        """Test report generation."""
        tool = MockTool()
        tester = ToolTester(tool)

        # Create mock results
        from wish_tools.framework.testing import TestResult

        mock_result = TestResult(
            test_case=TestCase(
                name="test",
                description="Test case",
                capability="echo",
                parameters={},
                expected_success=True,
                validators=[],
            ),
            passed=True,
            execution_time=0.1,
            tool_result=ToolResult(
                success=True, output="test output", error=None, exit_code=0, execution_time=0.1, metadata={}
            ),
            error=None,
            validation_errors=[],
        )

        report = tester.generate_report([mock_result])
        assert "# Test Report for mock" in report
        assert "✅ PASSED" in report
        assert "test output" in report


@pytest.mark.integration
class TestRealTools:
    """Integration tests with real tools (if available)."""

    @pytest.mark.asyncio
    async def test_bash_tool(self):
        """Test bash tool if available."""
        try:
            from wish_tools.tools.bash import BashTool

            tool = BashTool()
            is_available, _ = await tool.validate_availability()

            if is_available:
                with tempfile.TemporaryDirectory() as temp_dir:
                    context = ToolContext(working_directory=temp_dir, run_id="test")

                    command = CommandInput(command="echo 'test'", timeout_sec=30)
                    result = await tool.execute(command, context)

                    assert result.success is True
                    assert "test" in result.output
        except ImportError:
            pytest.skip("BashTool not available")

    @pytest.mark.asyncio
    async def test_tool_documentation_generation(self):
        """Test that all tools can generate documentation."""
        try:
            from wish_tools.tools import BashTool, MsfconsoleTool

            for tool_class in [BashTool, MsfconsoleTool]:
                tool = tool_class()
                docs = tool.get_documentation()

                # Basic documentation structure checks
                assert f"# {tool.metadata.name}" in docs
                assert "## Requirements" in docs
                assert "## Capabilities" in docs

        except ImportError:
            pytest.skip("Tool imports not available")


if __name__ == "__main__":
    pytest.main([__file__])
