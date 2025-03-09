# Contributing to wish

Thank you for your interest in contributing to wish! This document provides guidelines and instructions for contributing to this project.

## Development

Each package (`wish-*/`) contains its own README.md with specific development instructions.

## Updating the CHANGELOG

All notable changes to the wish project should be documented in the CHANGELOG.md file.

When making changes:

1. Add your changes to the `[Unreleased]` section of CHANGELOG.md
2. Categorize your changes under the appropriate heading:
   - `Added` for new features
   - `Changed` for changes in existing functionality
   - `Fixed` for bug fixes
   - `Removed` for removed features
3. Prefix your entry with the affected package name in square brackets, e.g., `[wish-models]`

Example:
```markdown
### Added
- [wish-models] New data model for command history
- [wish-sh] New UI component for displaying command suggestions
```

## Release Process

To release a new version:

1. Ensure all changes are properly documented in CHANGELOG.md
2. Use GitHub Actions UI: <https://github.com/SecDev-Lab/wish/actions/workflows/publish.yml>
3. Enter the new version number when prompted
4. The workflow will:
   - Update the version in all package pyproject.toml files
   - Build and publish the packages to PyPI
   - Update CHANGELOG.md by converting the Unreleased section to the new version
   - Create a GitHub release with the CHANGELOG content
