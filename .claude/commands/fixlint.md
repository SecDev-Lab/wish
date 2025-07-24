# +fixlint: Lint Fix Shortcut

This shortcut executes `make format` and automatically attempts to fix lint errors if they occur.

## Execution Command

```bash
make format
```

## Purpose

- Execute code formatting for all workspaces
- Automatically fix lint errors
- Ensure compliance with code quality standards

## Usage

```bash
+fixlint
```

## Fix Process

1. **Initial format execution**: Format all workspace code with `make format`
2. **Lint check**: Check for lint errors with `make lint`
3. **Auto-fix**: Automatically fix the following types of lint errors:
   - Import order errors
   - Unused imports
   - Line length violations
   - Indentation errors
   - Whitespace errors
   - Naming convention violations
   - Code style violations
   - Docstring format errors
4. **Re-run**: Execute lint check again after fixes
5. **Iterate**: Repeat steps 2-4 until all lint errors are resolved

## Target

- Entire wish source code

## Tools Used

- **ruff**: Fast Python linter/formatter
- **Auto-fix feature**: Automatic fixes via `ruff check --fix`

## Notes

- Formatting changes do not affect existing logic
- Some complex lint errors may require manual fixes
- Recommended to run before committing
- For large changes, review diffs before committing