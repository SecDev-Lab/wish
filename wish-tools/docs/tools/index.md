# Wish Tools Documentation

This directory contains automatically generated documentation for all available tools
in the wish-tools framework.

**Total Tools:** 2
**Categories:** 2

## Tools by Category

### Exploitation

- **[msfconsole](msfconsole.md)** - Metasploit Framework penetration testing tool

### Fallback

- **[bash](bash.md)** - Fallback shell command execution when no specialized tool is available

## Quick Reference

| Tool | Category | Description | Requirements |
|------|----------|-------------|--------------|
| [bash](bash.md) | fallback | Fallback shell command execution when no specialized tool is available | bash |
| [msfconsole](msfconsole.md) | exploitation | Metasploit Framework penetration testing tool | metasploit-framework |

## Usage Examples

### Basic Tool Usage

```python
from wish_tools.framework.registry import tool_registry
from wish_tools.framework.base import ToolContext, CommandInput

# Get a tool
tool = tool_registry.get_tool('bash')

# Create context
context = ToolContext(
    working_directory='/tmp',
    run_id='example'
)

# Execute command
command = CommandInput(command='echo hello', timeout_sec=30)
result = await tool.execute(command, context)

print(result.output)
```

### Generate Command from Capability

```python
# Generate command using tool capabilities
tool = tool_registry.get_tool('bash')
command = tool.generate_command(
    capability='execute',
    parameters={
        'command': 'nmap -sS -p 22,80,443 192.168.1.0/24',
        'category': 'network'
    }
)

print(command.command)  # nmap -sS -p 22,80,443 192.168.1.0/24
```

### Tool Testing

```python
from wish_tools.framework.testing import ToolTester, TestCase

# Create tester
tool = tool_registry.get_tool('bash')
tester = ToolTester(tool)

# Run availability test
result = await tester.test_availability()
print(f'Tool available: {result.passed}')

# Generate test report
results = await tester.run_test_suite(test_cases)
report = tester.generate_report(results)
print(report)
```

---

*Documentation generated automatically by wish-tools framework*