Investigate and fix CI failures for the Pull Request associated with the current branch.

Follow these steps:

1.  **Identify PR information**: Execute `gh pr list --head $(git branch --show-current)` to identify the PR number and URL associated with the current branch. If no PR is found, prompt the user to create a PR.

2.  **Check CI status**: Use `gh pr checks` to display a summary of CI status for the identified PR.

3.  **Analyze failure logs**: Combine `gh run list` and `gh run view --log-failed` to retrieve and display error logs from failed jobs in the latest workflow run.

4.  **Root cause analysis and fix proposal**:
    - Analyze the displayed error logs to identify the root cause of failures (e.g., test failures, lint errors, build issues).
    - Based on the identified cause, develop a specific fix strategy.
    - Present the fix strategy to the user and obtain approval before proceeding with code modifications.

5.  **Fix and verify**:
    - Modify code according to the approved strategy.
    - After fixes, run `make lint` and `make test` locally to verify the issues are resolved.

6.  **Commit and push**: Commit the fixes and push to remote to trigger CI re-run.