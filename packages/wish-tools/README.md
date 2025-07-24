# wish-tools

Penetration testing tool integration and output parsing for the wish platform.

## Overview

wish-tools provides a unified interface for integrating and managing various penetration testing tools within wish. It handles tool execution, output parsing, and result normalization.

## Key Features

- **Tool Abstraction**: Unified interface for different pentest tools
- **Output Parsing**: Structured parsing of tool outputs
- **Result Normalization**: Convert tool-specific formats to wish data models
- **Tool Discovery**: Automatic detection of available tools
- **Execution Management**: Safe and controlled tool execution

## Installation

```bash
# Install dependencies in development environment
uv sync --dev

# Install as package (future release)
pip install wish-tools
```

## Quick Start

### Basic Usage Example

```python
from wish_tools import ToolManager, NmapParser, NiktoParser
from wish_models import EngagementState

# Initialize tool manager
tool_manager = ToolManager()

# Check available tools
available_tools = tool_manager.discover_tools()
print(f"Available tools: {', '.join(available_tools)}")

# Execute nmap scan
result = await tool_manager.execute(
    tool="nmap",
    command="nmap -sS -sV -p- 192.168.1.100",
    timeout=300
)

# Parse results
parser = NmapParser()
hosts, services = parser.parse(result.stdout)

# Update engagement state
engagement = EngagementState(name="Example")
for host in hosts:
    engagement.hosts[host.id] = host
for service in services:
    host.add_service(service)
```

### Tool Integration Example

```python
from wish_tools import BaseTool, BaseParser

# Custom tool integration
class CustomTool(BaseTool):
    name = "custom-scanner"
    description = "Custom vulnerability scanner"
    
    def validate_command(self, command: str) -> bool:
        return command.startswith("custom-scanner")
    
    def build_command(self, target: str, options: dict) -> str:
        cmd = f"custom-scanner {target}"
        if options.get("aggressive"):
            cmd += " --aggressive"
        return cmd

# Custom parser
class CustomParser(BaseParser):
    def parse(self, output: str) -> dict:
        # Parse tool output
        findings = []
        for line in output.splitlines():
            if "VULN:" in line:
                findings.append(self.parse_vulnerability(line))
        return {"findings": findings}
```

## Supported Tools

### Network Scanners
- **Nmap**: Network discovery and service enumeration
- **Masscan**: High-speed port scanner
- **Zmap**: Internet-wide scanning

### Web Application Scanners
- **Nikto**: Web server scanner
- **Gobuster**: Directory/file brute-forcer
- **FFuf**: Web fuzzer
- **Nuclei**: Template-based scanner

### Vulnerability Scanners
- **OpenVAS**: Comprehensive vulnerability scanner
- **Nessus**: Commercial vulnerability scanner (API integration)

### Exploitation Tools
- **Metasploit**: Exploitation framework (via MSF RPC)
- **SQLMap**: SQL injection tool
- **Hydra**: Password brute-forcer

### Information Gathering
- **theHarvester**: OSINT gathering
- **Amass**: Subdomain enumeration
- **Shodan**: API integration for passive scanning

## Architecture

### Core Components

#### ToolManager
Central manager for all tool operations.

```python
from wish_tools import ToolManager

manager = ToolManager()

# Discover tools
tools = manager.discover_tools()

# Execute tool
result = await manager.execute(
    tool="nmap",
    command="nmap -sn 192.168.1.0/24",
    working_dir="/tmp"
)

# Get tool info
info = manager.get_tool_info("nmap")
print(f"Tool: {info.name}")
print(f"Version: {info.version}")
print(f"Available: {info.is_available}")
```

#### Parser System
Modular parsing system for tool outputs.

```python
from wish_tools.parsers import ParserRegistry

# Register custom parser
registry = ParserRegistry()
registry.register("custom-tool", CustomParser)

# Get parser for tool
parser = registry.get_parser("nmap")
results = parser.parse(tool_output)
```

#### Result Normalization
Convert tool outputs to wish data models.

```python
from wish_tools.normalizers import ResultNormalizer

normalizer = ResultNormalizer()

# Normalize nmap results
nmap_results = {"hosts": [...], "services": [...]}
normalized = normalizer.normalize("nmap", nmap_results)

# Returns wish_models objects
for host in normalized.hosts:
    print(f"Host: {host.ip_address}")
```

## Development Guide

### Adding New Tools

1. Create a new tool class:
```python
from wish_tools.base import BaseTool

class NewTool(BaseTool):
    name = "newtool"
    description = "Description of the tool"
    required_binaries = ["newtool"]
    
    def validate_command(self, command: str) -> bool:
        # Validate command syntax
        return True
    
    def build_command(self, target: str, options: dict) -> str:
        # Build command from parameters
        return f"newtool {target}"
```

2. Create a parser:
```python
from wish_tools.base import BaseParser

class NewToolParser(BaseParser):
    def parse(self, output: str) -> dict:
        # Parse tool output
        return parsed_data
```

3. Register the tool and parser:
```python
from wish_tools import register_tool, register_parser

register_tool(NewTool)
register_parser("newtool", NewToolParser)
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/test_nmap_parser.py

# Run integration tests
uv run pytest tests/integration/
```

### Project Structure

```
packages/wish-tools/
├── src/wish_tools/
│   ├── __init__.py           # Package exports
│   ├── base.py               # Base classes
│   ├── manager.py            # Tool manager
│   ├── tools/                # Tool implementations
│   │   ├── __init__.py
│   │   ├── nmap.py
│   │   ├── nikto.py
│   │   └── ...
│   ├── parsers/              # Output parsers
│   │   ├── __init__.py
│   │   ├── nmap_parser.py
│   │   ├── nikto_parser.py
│   │   └── ...
│   └── normalizers/          # Result normalizers
│       ├── __init__.py
│       └── base.py
├── tests/
│   ├── test_tool_manager.py
│   ├── test_parsers/
│   └── fixtures/             # Sample tool outputs
└── README.md
```

## Configuration

### Tool Paths
Configure custom tool paths in `~/.wish/config.toml`:

```toml
[tools.paths]
nmap = "/usr/local/bin/nmap"
nikto = "/opt/nikto/nikto.pl"
custom-scanner = "/home/user/tools/scanner"

[tools.defaults]
timeout = 300  # Default timeout in seconds
working_dir = "/tmp/wish-tools"
```

### Execution Limits
Set resource limits for tool execution:

```toml
[tools.limits]
max_concurrent = 5          # Max concurrent tool executions
max_memory_mb = 2048       # Memory limit per tool
max_cpu_percent = 80       # CPU usage limit
```

## Security Considerations

- **Command Injection**: All commands are validated and sanitized
- **Resource Limits**: Memory and CPU limits prevent resource exhaustion
- **Sandboxing**: Optional sandbox mode for untrusted tools
- **Output Validation**: Parser output is validated against schemas

## License

This project is published under [appropriate license].

## Related Packages

- `wish-models`: Core data models and validation
- `wish-core`: State management and event processing
- `wish-ai`: AI-driven inference engine
- `wish-knowledge`: Knowledge base management
- `wish-c2`: C2 server integration
- `wish-cli`: Command line interface

## Support

If you have issues or questions, you can get support through:

- [Issues](../../issues): Bug reports and feature requests
- [Discussions](../../discussions): General questions and discussions
- Documentation: Tool integration guides and parser documentation