# +fixtest: Test Fix Shortcut

This shortcut executes `make test` and automatically attempts to fix test errors if they occur.

## Execution Command

```bash
make test
```

## Purpose

- Execute unit tests for all workspaces
- Automatically fix test errors
- Iterate until all tests pass

## Usage

```bash
+fixtest
```

## Fix Process

1. **Initial test execution**: Run tests for all workspaces with `make test`
2. **Error analysis**: Identify the cause of failed tests
3. **Auto-fix**: Automatically fix the following types of errors:
   - Import errors
   - Errors due to module name changes
   - Errors due to package structure changes
   - Type errors
   - Syntax errors
   - Dependency errors
4. **Re-run**: Execute tests again after fixes
5. **Iterate**: Repeat steps 2-4 until all tests pass

## Target

- Entire wish test suite

## Notes

- LLM tests (`@pytest.mark.llm`) are excluded
- Time-consuming tests (`@pytest.mark.slow`) are excluded
- Test fixes are executed carefully to avoid breaking existing logic
- Complex business logic errors may require manual review