# +e2e: End-to-End Test Execution

This shortcut executes phased end-to-end tests for wish-cli-basic-ui.

## Execution Command

```bash
make e2e
```

## Usage

```bash
+e2e    # wish CLI e2e test (all phases)
```

## Test Configuration

### Level 1: Component Integration Tests
- ✅ Basic application startup/shutdown tests
- ✅ `/help` command functionality verification
- ✅ `/status` command functionality verification
- ✅ `/mode` command functionality verification

### Level 2: Workflow Integration Tests
- ✅ Invalid command error handling
- ✅ Invalid mode error handling
- ✅ Multiple command sequential execution
- ✅ Session state consistency verification
- ✅ Recovery functionality after errors

## Execution Methods

**Execute from Claude Code:**
```bash
+e2e
```

**Phased execution:**
```bash
make e2e-component    # Level 1 only
make e2e-workflow     # Level 2 only
make e2e             # All phases
```

**Direct pytest execution:**
```bash
uv run pytest e2e-tests/component/ -v
uv run pytest e2e-tests/workflows/ -v
```

## Test Result Interpretation

### Success Output Example
```
🚀 Starting wish-cli-basic-ui E2E Tests
==================================================
🧪 Running: test_basic_startup
✅ PASS basic_startup (2.31s): Application started and exited successfully
🧪 Running: test_help_command
✅ PASS help_command (1.87s): Help command displayed expected content
...
✅ ALL TESTS PASSED
```

### Handling Failures

**Common Issues:**
1. **Startup failure**: Reinstall dependencies with `uv sync --dev`
2. **Timeout**: Check system load
3. **Command errors**: Verify latest code is deployed

**Debug Methods:**
```bash
# Run tests with detailed output
python scripts/e2e_test.py --verbose

# Manual functionality verification
uv run wish
```

## Continuous Quality Management

This E2E test is executed in the following situations:
- Functionality verification after adding new features
- Regression testing after bug fixes
- Quality verification before PR creation
- Automated execution in CI/CD pipeline

## Expected Behavior

- **All tests pass**: Basic functionality working normally
- **Partial failures**: Related functionality needs fixing
- **All tests fail**: Possible basic environment issues

## Notes

- Test execution time: Approximately 10-30 seconds
- Minimal external dependencies (uses mocks)
- No actual network connection required
- Environment cleanup is automatic