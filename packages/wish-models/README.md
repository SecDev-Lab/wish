# wish-models

Core data models package for the wish penetration testing support system.

## Overview

wish-models provides type-safe data models based on Pydantic v2 for managing the entire penetration testing engagement state and tracking relationships.

## Key Features

- **Type-safe data models**: Powerful validation with Pydantic v2
- **Relationship management**: Bidirectional tracking between Finding ↔ CollectedData
- **Comprehensive validation**: Specialized validation for IPs, ports, CVEs, etc.
- **Automatic statistics calculation**: Dynamic aggregation of active hosts, open services, etc.
- **Session management**: Lightweight metadata management

## Installation

```bash
# Install dependencies in development environment
uv sync --dev

# Install as package (future release)
pip install wish-models
```

## Quick Start

### Basic Usage Example

```python
from wish_models import EngagementState, Target, Host, Service, Finding, CollectedData, SessionMetadata

# Create session information
session = SessionMetadata(engagement_name="Example Pentest")

# Initialize engagement state
engagement = EngagementState(name="Example Engagement", session_metadata=session)

# Add target
target = Target(scope="192.168.1.0/24", scope_type="cidr", name="Internal Network")
engagement.add_target(target)

# Discover host
host = Host(
    ip_address="192.168.1.100",
    status="up",
    discovered_by="nmap"
)
engagement.hosts[host.id] = host

# Discover service
service = Service(
    host_id=host.id,
    port=80,
    protocol="tcp",
    state="open",
    service_name="http",
    discovered_by="nmap"
)
host.add_service(service)

# Register finding
finding = Finding(
    title="Unpatched Web Server",
    description="Apache 2.2.x with known vulnerabilities",
    category="vulnerability",
    severity="high",
    target_type="service",
    host_id=host.id,
    service_id=service.id,
    discovered_by="nikto"
)
finding.add_cve("CVE-2021-44228")  # Log4j vulnerability
engagement.findings[finding.id] = finding

# Manage collected data
credentials = CollectedData(
    type="credentials",
    content="admin:password123",
    username="admin",
    source_host_id=host.id,
    source_service_id=service.id,
    source_finding_id=finding.id,
    discovered_by="hydra",
    working=True
)
engagement.collected_data[credentials.id] = credentials

# Establish relationships
finding.link_collected_data(credentials.id)
credentials.add_derived_finding(finding.id)

# Get statistics
active_hosts = engagement.get_active_hosts()
open_services = engagement.get_open_services()
working_creds = engagement.get_working_credentials()

print(f"Active hosts: {len(active_hosts)}")
print(f"Open services: {len(open_services)}")
print(f"Working credentials: {len(working_creds)}")
```

### Validation Example

```python
from wish_models.validation import (
    validate_ip_address,
    validate_port,
    validate_cve_id,
    ValidationError
)

# IP address validation
ip_result = validate_ip_address("192.168.1.1")
if ip_result.is_valid:
    print(f"Valid IP: {ip_result.data}")
else:
    print(f"Invalid IP: {ip_result.errors}")

# Port number validation
try:
    port_result = validate_port(80)
    valid_port = port_result.raise_if_invalid()
    print(f"Valid port: {valid_port}")
except ValidationError as e:
    print(f"Port validation failed: {e}")

# CVE ID validation
cve_result = validate_cve_id("CVE-2021-44228")
print(f"CVE validation: {cve_result.is_valid}")
```

## Data Model Details

### Main Models

| Model | Description | Key Fields |
|-------|-------------|------------|
| `EngagementState` | Overall engagement state | targets, hosts, findings, collected_data |
| `Target` | Pentest target definition | scope, scope_type, in_scope |
| `Host` | Discovered host information | ip_address, status, services |
| `Service` | Service on host | port, protocol, state, service_name |
| `Finding` | Vulnerability/discovery | title, category, severity, cve_ids |
| `CollectedData` | Collected important data | type, content, is_sensitive, working |
| `SessionMetadata` | Session management info | current_mode, command_history |

### Validation Features

- **Network**: IP, CIDR, MAC, port numbers
- **Security**: CVE ID, URL format
- **Data integrity**: Confidence scores, datetime constraints
- **Relationships**: Cross-model reference integrity checks

## Development Guide

### Running Tests

```bash
# Run all tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/test_models_core.py

# Run with verbose output
uv run pytest -v
```

### Code Quality Checks

```bash
# Run linting
uv run ruff check src/ tests/

# Format code
uv run ruff format src/ tests/

# Type checking (mypy)
uv run mypy src/
```

### Project Structure

```
packages/wish-models/
├── src/wish_models/
│   ├── __init__.py          # Package exports
│   ├── engagement.py        # EngagementState, Target
│   ├── host.py             # Host, Service  
│   ├── finding.py          # Finding
│   ├── data.py             # CollectedData
│   ├── session.py          # SessionMetadata
│   └── validation.py       # Validation functions
├── tests/
│   ├── test_models_core.py      # Individual model tests
│   ├── test_engagement_state.py # EngagementState tests
│   ├── test_relationships.py    # Relationship tests
│   ├── test_validation.py       # Validation class tests
│   └── test_validation_functions.py # Validation function tests
├── docs/
│   ├── implementation.md        # Implementation specification
│   └── design-decisions.md     # Design decision records
└── README.md
```

### Contributing Guide

1. **Fork**: Fork the repository
2. **Create branch**: `git checkout -b feature/your-feature`
3. **Implement**: Add features or fixes
4. **Test**: Ensure all tests pass
5. **Quality check**: Run lint and format
6. **Pull request**: Create PR to main repository

### Testing Guidelines

- **Unit tests**: Test individual model functionality
- **Validation tests**: Test both valid and invalid values
- **Relationship tests**: Test interactions between models
- **Boundary tests**: Focus on validation boundary values

## API Reference

For detailed API specifications, please refer to the following documents:

- [Implementation Specification](docs/implementation.md) - Detailed implementation
- [Design Decision Records](docs/design-decisions.md) - Architecture decision records

## Performance

### Test Results

- **Test count**: 113 tests
- **Success rate**: 100%
- **Coverage**: 94%
- **Warnings**: 0

### Optimization Points

- Fast validation with Pydantic v2
- Reduced computational cost through lazy evaluation
- Automatic duplicate data elimination
- Memory-efficient ID-based references

## License

This project is published under [appropriate license].

## Related Packages

- `wish-core`: State management and event processing
- `wish-ai`: AI-driven inference engine
- `wish-tools`: Pentest tool integration
- `wish-knowledge`: Knowledge base management
- `wish-c2`: C2 server integration
- `wish-cli`: Command line interface

## Support

If you have issues or questions, you can get support through:

- [Issues](../../issues): Bug reports and feature requests
- [Discussions](../../discussions): General questions and discussions
- Documentation: Review implementation specifications and design records