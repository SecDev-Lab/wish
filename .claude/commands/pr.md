Create a Pull Request from the current branch to the `main` branch following best practices.
If `draft` is specified in `$ARGUMENTS`, create as a draft PR.

Follow these steps:

1.  **Pre-checks**:
    - Use `git status` to check for uncommitted changes. If any exist, ask the user whether to commit or stash them.
    - Use `git branch --show-current` to verify the current branch name is not `main` or `master`.

2.  **Sync with remote**:
    - Execute `git fetch origin`.
    - If the local branch doesn't exist on remote or has unpushed commits, execute `git push -u origin $(git branch --show-current)` to sync with remote.

3.  **Generate PR information**:
    - **Title**: If there's only one commit in the diff with `main` branch, use the first line of that commit message as the title. If there are multiple commits, convert the branch name to a human-readable format (e.g., `feat/new-feature` -> `Feat: New Feature`) for the title.
    - **Body**: Include the list of commits in the diff with `main` branch in bullet point format. Also provide template sections for "Related Issues" and "Testing".

4.  **Create PR**:
    - Use the `gh pr create` command to create the PR.
    - If `$ARGUMENTS` contains `draft`, add the `--draft` flag.