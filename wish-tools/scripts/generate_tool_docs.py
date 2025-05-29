#!/usr/bin/env python3
"""
Tool documentation generator for wish-tools.

This script automatically generates documentation for all available tools
in the wish-tools framework.
"""

import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from wish_tools.framework.registry import tool_registry


def generate_individual_docs(output_dir: Path):
    """Generate individual documentation files for each tool."""
    output_dir.mkdir(parents=True, exist_ok=True)

    tools = tool_registry.list_tools()
    print(f"Generating documentation for {len(tools)} tools...")

    for tool_metadata in tools:
        try:
            # Get tool instance
            tool = tool_registry.get_tool(tool_metadata.name)

            # Generate documentation
            docs = tool.get_documentation()

            # Write to file
            doc_file = output_dir / f"{tool_metadata.name}.md"
            with open(doc_file, "w") as f:
                f.write(docs)

            print(f"Generated: {doc_file}")

        except Exception as e:
            print(f"Error generating docs for {tool_metadata.name}: {e}")


def generate_index_docs(output_dir: Path):
    """Generate an index file listing all available tools."""
    index_file = output_dir / "index.md"

    tools = tool_registry.list_tools()

    # Group tools by category
    categories = {}
    for tool in tools:
        if tool.category not in categories:
            categories[tool.category] = []
        categories[tool.category].append(tool)

    # Generate index content
    content = [
        "# Wish Tools Documentation",
        "",
        "This directory contains automatically generated documentation for all available tools",
        "in the wish-tools framework.",
        "",
        f"**Total Tools:** {len(tools)}",
        f"**Categories:** {len(categories)}",
        "",
        "## Tools by Category",
        "",
    ]

    for category, category_tools in sorted(categories.items()):
        content.append(f"### {category.title()}")
        content.append("")

        for tool in sorted(category_tools, key=lambda t: t.name):
            content.append(f"- **[{tool.name}]({tool.name}.md)** - {tool.description}")

        content.append("")

    # Add quick reference
    content.extend(
        [
            "## Quick Reference",
            "",
            "| Tool | Category | Description | Requirements |",
            "|------|----------|-------------|--------------|",
        ]
    )

    for tool in sorted(tools, key=lambda t: t.name):
        requirements = ", ".join(tool.requirements) if tool.requirements else "None"
        content.append(f"| [{tool.name}]({tool.name}.md) | {tool.category} | {tool.description} | {requirements} |")

    content.extend(
        [
            "",
            "## Usage Examples",
            "",
            "### Basic Tool Usage",
            "",
            "```python",
            "from wish_tools.framework.registry import tool_registry",
            "from wish_tools.framework.base import ToolContext, CommandInput",
            "",
            "# Get a tool",
            "tool = tool_registry.get_tool('bash')",
            "",
            "# Create context",
            "context = ToolContext(",
            "    working_directory='/tmp',",
            "    run_id='example'",
            ")",
            "",
            "# Execute command",
            "command = CommandInput(command='echo hello', timeout_sec=30)",
            "result = await tool.execute(command, context)",
            "",
            "print(result.output)",
            "```",
            "",
            "### Generate Command from Capability",
            "",
            "```python",
            "# Generate command using tool capabilities",
            "tool = tool_registry.get_tool('bash')",
            "command = tool.generate_command(",
            "    capability='execute',",
            "    parameters={",
            "        'command': 'nmap -sS -p 22,80,443 192.168.1.0/24',",
            "        'category': 'network'",
            "    }",
            ")",
            "",
            "print(command.command)  # nmap -sS -p 22,80,443 192.168.1.0/24",
            "```",
            "",
            "### Tool Testing",
            "",
            "```python",
            "from wish_tools.framework.testing import ToolTester, TestCase",
            "",
            "# Create tester",
            "tool = tool_registry.get_tool('bash')",
            "tester = ToolTester(tool)",
            "",
            "# Run availability test",
            "result = await tester.test_availability()",
            "print(f'Tool available: {result.passed}')",
            "",
            "# Generate test report",
            "results = await tester.run_test_suite(test_cases)",
            "report = tester.generate_report(results)",
            "print(report)",
            "```",
            "",
            "---",
            "",
            "*Documentation generated automatically by wish-tools framework*",
        ]
    )

    with open(index_file, "w") as f:
        f.write("\n".join(content))

    print(f"Generated index: {index_file}")


def generate_capability_matrix(output_dir: Path):
    """Generate a capability matrix showing what each tool can do."""
    matrix_file = output_dir / "capability-matrix.md"

    tools = tool_registry.list_tools()

    # Collect all unique capabilities
    all_capabilities = set()
    tool_capabilities = {}

    for tool in tools:
        capabilities = [cap.name for cap in tool.capabilities]
        tool_capabilities[tool.name] = capabilities
        all_capabilities.update(capabilities)

    all_capabilities = sorted(all_capabilities)

    content = [
        "# Tool Capability Matrix",
        "",
        "This matrix shows which capabilities are available for each tool.",
        "",
        "| Tool | " + " | ".join(all_capabilities) + " |",
        "|------|" + "|".join("---" for _ in all_capabilities) + "|",
    ]

    for tool in sorted(tools, key=lambda t: t.name):
        row = [f"**{tool.name}**"]
        for capability in all_capabilities:
            if capability in tool_capabilities[tool.name]:
                row.append("✅")
            else:
                row.append("❌")
        content.append("| " + " | ".join(row) + " |")

    content.extend(
        [
            "",
            "## Legend",
            "",
            "- ✅ = Capability available",
            "- ❌ = Capability not available",
            "",
            "## Capability Descriptions",
            "",
        ]
    )

    # Add capability descriptions
    capability_descriptions = {}
    for tool in tools:
        for cap in tool.capabilities:
            if cap.name not in capability_descriptions:
                capability_descriptions[cap.name] = cap.description

    for capability in sorted(capability_descriptions.keys()):
        content.append(f"- **{capability}**: {capability_descriptions[capability]}")

    with open(matrix_file, "w") as f:
        f.write("\n".join(content))

    print(f"Generated capability matrix: {matrix_file}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate documentation for wish-tools")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).parent.parent / "docs" / "tools",
        help="Output directory for documentation",
    )
    parser.add_argument("--individual", action="store_true", help="Generate individual tool documentation files")
    parser.add_argument("--index", action="store_true", help="Generate index documentation")
    # Capability matrix removed - misleading about bash capabilities
    # parser.add_argument(
    #     "--matrix",
    #     action="store_true",
    #     help="Generate capability matrix"
    # )

    args = parser.parse_args()

    # If no specific options, generate all available
    if not any([args.individual, args.index]):
        args.individual = True
        args.index = True

    print(f"Generating documentation in: {args.output_dir}")

    # Auto-discover tools
    try:
        tool_registry.auto_discover_tools("wish_tools.tools")
        print(f"Discovered {len(tool_registry.get_tool_names())} tools")
    except Exception as e:
        print(f"Warning: Tool auto-discovery failed: {e}")

    # Generate documentation
    if args.individual:
        generate_individual_docs(args.output_dir)

    if args.index:
        generate_index_docs(args.output_dir)

    # Capability matrix removed - it was misleading about bash capabilities
    # if args.matrix:
    #     generate_capability_matrix(args.output_dir)

    print("Documentation generation complete!")


if __name__ == "__main__":
    main()
