# +brc - Branch Review & Cleanup

Review differences between current branch and main branch, and perform branch cleanup.

## Overview

This command performs comprehensive quality checks and cleanup before PR creation. It focuses on:

- Ensuring code quality (lint, format)
- Removing unnecessary files and code
- **Complete cleanup of tmp/ directory**
- Reviewing and resolving TODOs
- Ensuring test success

## Execution Steps

### 1. Review Differences
```bash
git diff main...HEAD
git diff --name-only main...HEAD
```
Review files and content changed in the current branch.

### 2. Remove Unnecessary Files and Code Fragments
- Remove debug print statements, console.log, temporary commented-out code
- Remove temporary test files (test_*.py, *.log, *.tmp, etc.) not used in actual tests
- Remove unused import statements
- Remove experimental code only used during implementation
- **tmp/ directory cleanup**:
  ```bash
  # Check tmp/ directory contents
  if [ -d "tmp/" ]; then
    echo "=== tmp/ directory contents ==="
    ls -la tmp/
    echo "Delete these files? (y/N)"
    # Wait for user confirmation
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
      rm -rf tmp/*
      echo "Cleaned up tmp/ directory"
    fi
  else
    echo "tmp/ directory does not exist"
  fi
  ```

### 3. Review and Resolve TODOs
```bash
# Search for TODO comments
rg "TODO|FIXME|XXX|HACK" --type-add 'code:*.{py,ts,js,tsx,jsx}' -t code
```
- Review each TODO found
- Immediately resolve items that should be addressed in current branch
- For items to remain as future tasks, clearly document reasons in summary

### 4. Fix Formatting
```bash
make format
make lint
```
- If lint errors exist, review error messages and fix
- Manually fix errors that cannot be auto-fixed

### 5. Fix Tests
```bash
make test
```
- If tests fail:
  - First analyze error messages
  - Verify test expectations are correct
  - Determine whether to fix implementation or tests
  - If implementation should take priority over tests, document reasons in summary

### 6. Final Review and Summary Display
Display summary in the following format:

```
## Branch Review Summary

### Changes
- Changed files: X files
- Added lines: +XXX
- Deleted lines: -XXX

### Cleanup Performed
- [ ] Removed unnecessary debug code
- [ ] Removed unused imports
- [ ] Removed temporary files
- [ ] Cleaned up tmp/ directory

### TODO Status
- Resolved: X items
- Remaining: X items
  - [Reason] TODO content

### Test & Quality Check
- [ ] make format: PASS/FAIL
- [ ] make lint: PASS/FAIL  
- [ ] make test: PASS/FAIL

### Remaining Issues
(Document if any)

### Next Steps
(If all checks PASS)
Ready to create PR. Create PR with the following command:
gh pr create --title "Title" --body "Description"
```

## Notes
- Carefully judge unnecessary code to not compromise implementation intent
- If tests fail, don't hastily fix tests; prioritize verifying implementation correctness
- Don't automatically create PR; prompt for user's final confirmation
- **About tmp/ directory**:
  - All intermediate files created by Claude Code (test files, planning documents, etc.) are placed in tmp/
  - Always perform cleanup when executing +brc
  - Request user confirmation before deletion