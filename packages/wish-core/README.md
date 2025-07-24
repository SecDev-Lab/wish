# wish-core

Core business logic and state management for the wish penetration testing support system.

## Overview

wish-core provides the central business logic, state management, and event processing capabilities for wish. It acts as the coordination layer between the AI components, tools, and user interface.

## Key Features

- **State Management**: Centralized management of engagement state and session data
- **Event System**: Event-driven architecture for component communication
- **Tool Coordination**: Integration layer for penetration testing tools
- **Workflow Management**: Handles the flow between different testing phases
- **Job Management**: Asynchronous job execution and monitoring

## Installation

```bash
# Install dependencies in development environment
uv sync --dev

# Install as package (future release)
pip install wish-core
```

## Quick Start

### Basic Usage Example

```python
from wish_core import StateManager, EventBus, JobManager
from wish_models import EngagementState, SessionMetadata

# Initialize core components
state_manager = StateManager()
event_bus = EventBus()
job_manager = JobManager()

# Create and manage engagement state
session = SessionMetadata(engagement_name="Example Pentest")
engagement = EngagementState(name="Internal Network Assessment", session_metadata=session)
state_manager.set_engagement(engagement)

# Subscribe to events
@event_bus.subscribe("host.discovered")
async def on_host_discovered(event):
    print(f"New host discovered: {event.data['ip_address']}")

# Execute tools asynchronously
job = await job_manager.execute_tool(
    tool_name="nmap",
    command="nmap -sS -p- 192.168.1.0/24",
    callback=lambda result: process_nmap_results(result)
)

# Monitor job progress
status = await job_manager.get_job_status(job.id)
print(f"Job {job.id} status: {status}")
```

## Architecture

### Core Components

#### StateManager
Manages the central engagement state and provides thread-safe access to shared data.

```python
from wish_core import StateManager

manager = StateManager()

# Get current state
state = manager.get_current_state()

# Update specific parts
manager.update_hosts(new_hosts)
manager.add_finding(finding)

# Transaction support
with manager.transaction():
    manager.update_hosts(hosts)
    manager.update_services(services)
```

#### EventBus
Provides event-driven communication between components.

```python
from wish_core import EventBus

bus = EventBus()

# Subscribe to events
@bus.subscribe("tool.completed")
async def handle_tool_completion(event):
    print(f"Tool {event.data['tool']} completed")

# Publish events
await bus.publish("scan.started", {"target": "192.168.1.0/24"})
```

#### JobManager
Handles asynchronous execution of tools and long-running operations.

```python
from wish_core import JobManager

job_manager = JobManager()

# Execute tool
job = await job_manager.execute_tool(
    tool_name="nikto",
    command="nikto -h http://target.com",
    timeout=300
)

# Check status
status = await job_manager.get_job_status(job.id)

# Cancel job
await job_manager.cancel_job(job.id)
```

## Development Guide

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/test_state_manager.py

# Run with verbose output
uv run pytest -v
```

### Code Quality Checks

```bash
# Run linting
uv run ruff check src/ tests/

# Format code
uv run ruff format src/ tests/

# Type checking
uv run mypy src/
```

### Project Structure

```
packages/wish-core/
├── src/wish_core/
│   ├── __init__.py           # Package exports
│   ├── state_manager.py      # State management
│   ├── event_bus.py          # Event system
│   ├── job_manager.py        # Job execution
│   ├── workflow/             # Workflow management
│   │   ├── __init__.py
│   │   └── coordinator.py
│   └── utils/                # Utility functions
│       ├── __init__.py
│       └── threading.py
├── tests/
│   ├── test_state_manager.py
│   ├── test_event_bus.py
│   ├── test_job_manager.py
│   └── test_workflow.py
└── README.md
```

## API Reference

### StateManager API

- `get_current_state()`: Get the current engagement state
- `set_engagement(engagement)`: Set a new engagement
- `update_hosts(hosts)`: Update host information
- `add_finding(finding)`: Add a new finding
- `transaction()`: Context manager for atomic updates

### EventBus API

- `subscribe(event_type, handler)`: Subscribe to an event type
- `unsubscribe(event_type, handler)`: Unsubscribe from events
- `publish(event_type, data)`: Publish an event
- `clear()`: Clear all subscriptions

### JobManager API

- `execute_tool(tool_name, command, **kwargs)`: Execute a tool
- `get_job_status(job_id)`: Get job status
- `cancel_job(job_id)`: Cancel a running job
- `get_job_logs(job_id)`: Get job output logs
- `list_active_jobs()`: List all active jobs

## License

This project is published under [appropriate license].

## Related Packages

- `wish-models`: Core data models and validation
- `wish-ai`: AI-driven inference engine
- `wish-tools`: Pentest tool integration
- `wish-knowledge`: Knowledge base management
- `wish-c2`: C2 server integration
- `wish-cli`: Command line interface

## Support

If you have issues or questions, you can get support through:

- [Issues](../../issues): Bug reports and feature requests
- [Discussions](../../discussions): General questions and discussions
- Documentation: Review API documentation and examples