# E2E Test Implementation Guide

## Overview

wish's E2E tests adopt a **headless mode-centric** approach. Using the HeadlessWish Python SDK, we achieve fast and reliable testing.

## Test Hierarchy

### Level 1: Component Integration Tests (`component/`)
- **Purpose**: Basic inter-package integration verification
- **Execution Time**: < 30 seconds
- **Targets**:
  - `test_state_management.py` - State management functionality
  - `test_ai_integration.py` - AI integration functionality
  - `test_tool_execution.py` - Tool execution functionality

### Level 2: Workflow Integration Tests (`workflows/`)
- **Purpose**: Major penetration testing workflow verification
- **Execution Time**: < 2 minutes
- **Targets**:
  - `test_scan_workflow.py` - Scan workflow

### Level 3: Scenario-Based Tests (`scenarios/`)
- **Purpose**: Comprehensive operation verification in actual pentest scenarios
- **Execution Time**: < 5 minutes (mock environment)
- **Targets**:
  - `test_htb_lame.py` - HTB Lame scenario

### AI Quality Verification Tests (`quality/`)
- **Purpose**: AI response quality and safety verification
- **Execution Time**: < 1 minute
- **Targets**:
  - `test_ai_quality.py` - AI quality metrics

## Execution Methods

### Basic Execution

```bash
# Run all E2E tests
make e2e

# Phased execution
make e2e-component    # Level 1
make e2e-workflow     # Level 2
make e2e-scenario     # Level 3
make e2e-quality      # AI quality
```

### Detailed Execution

```bash
# Specific test file
uv run pytest e2e-tests/component/test_state_management.py -v

# Specific test class
uv run pytest e2e-tests/scenarios/test_htb_lame.py::TestHTBLameScenario -v

# Specific test method
uv run pytest e2e-tests/workflows/test_scan_workflow.py::TestScanWorkflow::test_scan_to_suggestion_workflow -v

# Pattern matching
uv run pytest e2e-tests/ -k "scan" -v
```

## Writing Tests

### Basic Pattern

```python
import pytest
from wish_cli.headless import HeadlessWish
from e2e_tests.fixtures import setup_mocks

class TestMyFeature:
    @pytest.mark.asyncio
    async def test_basic_functionality(self):
        # Initialize HeadlessWish
        wish = HeadlessWish(auto_approve=True)
        wish = setup_mocks(wish)
        
        # Start session
        session = await wish.start_session()
        
        try:
            # Execute test
            result = await session.send_prompt("test command")
            
            # Verify
            assert result.result is not None
            
        finally:
            # End session
            await session.end()
```

### Event Handling

```python
from wish_core.events.bus import EventType
from e2e_tests.fixtures import MockEventCollector

@pytest.mark.asyncio
async def test_with_events(self):
    wish = HeadlessWish(auto_approve=True)
    wish = setup_mocks(wish)
    
    # Event collector
    collector = MockEventCollector()
    
    @wish.on_event(EventType.PLAN_APPROVAL_REQUIRED)
    async def handle_approval(event):
        collector.collect_plan_approval(event)
        return "approve"
    
    session = await wish.start_session()
    
    try:
        await session.send_prompt("generate plan")
        
        # Verify events
        assert len(collector.plan_approvals) > 0
        
    finally:
        await session.end()
```

## Mocks and Fixtures

### Available Mocks (`fixtures/mocks.py`)

- **MockLLMService**: Deterministic AI response mocking
- **MockToolExecutor**: Tool execution result mocking
- **MockEventCollector**: Event collection and verification
- **setup_mocks()**: Apply mocks to HeadlessWish

### Test Data (`fixtures/data.py`)

- **MOCK_NMAP_OUTPUT**: Nmap scan results
- **HTB_LAME_SCENARIO**: HTB Lame scenario data
- **sample_host()**: Generate sample host
- **sample_finding()**: Generate sample vulnerability finding
- **DANGEROUS_PATTERNS**: Dangerous command patterns

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/e2e-tests.yml
- name: Run E2E Tests
  run: |
    make e2e-component
    make e2e-workflow
    make e2e-quality
```

### Quality Gates

- **Component Tests**: 100% pass required
- **Workflow Tests**: 90% pass required
- **AI Quality Metrics**: Above threshold required

## TUI Testing (Minimal)

Test TUI-specific elements separately:

```bash
# Create TUI test directory (if needed)
mkdir e2e-tests/tui

# Run TUI-specific tests
make e2e-tui
```

## Debugging and Troubleshooting

### Verbose Log Output

```bash
# Run tests with detailed logs
uv run pytest e2e-tests/ -v -s --log-cli-level=DEBUG
```

### Run Only Failed Tests

```bash
# Re-run only failed tests
uv run pytest e2e-tests/ --lf -v
```

### Test Timeout

```bash
# Specify timeout value
uv run pytest e2e-tests/ --timeout=600
```

## Development Notes

1. **Use HeadlessWish**: Use HeadlessWish SDK for all tests
2. **Apply Mocks**: Always execute `setup_mocks(wish)`
3. **Session Management**: Ensure session termination with `try-finally`
4. **Event Verification**: Test with event handlers as needed
5. **State Verification**: Confirm state changes with `session.get_state()`

## Performance Goals

- **Component**: Each test < 10 seconds
- **Workflow**: Each test < 30 seconds
- **Scenario**: Each test < 2 minutes
- **Quality**: Each test < 15 seconds

This implementation ensures wish's E2E tests are fast, reliable, and maintainable.