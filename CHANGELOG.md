# Changelog

All notable changes to the wish project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Added error modal for command generation failures:
  - Improved error handling to display errors in a modal dialog instead of command suggestion screen
  - Enhanced user experience by keeping users in the wish input screen when errors occur
  - Added detailed error information display including the command generation response

### Changed

### Fixed

- Fixed embedding model configuration in wish-knowledge-loader:
  - Updated vector_store.py to use OPENAI_EMBEDDING_MODEL instead of OPENAI_MODEL for embeddings
  - Added OPENAI_EMBEDDING_MODEL configuration to .env.example
  - Updated docs/setup.md with instructions for setting up OPENAI_EMBEDDING_MODEL
  - Fixed "You are not allowed to generate embeddings from this model" error
- Fixed JSON parsing in command generation:
  - Added explicit instruction to avoid code block markers like ```json in the prompt
  - Improved prompt to clarify that output is parsed directly as JSON
  - Enhanced error handling for invalid JSON responses

### Removed


## [0.4.0] - 2025-03-09

### Added

- Added comprehensive whitepaper:
  - `docs/whitepaper.md`: Technical whitepaper describing wish architecture, features, and development roadmap
  - Detailed comparison with similar tools in the penetration testing space
  - Explanation of wish's role in the RapidPen ecosystem
- Added knowledge management features to wish-knowledge-loader:
  - New `list` command to display all loaded knowledge bases
  - New `delete` command to remove knowledge bases when no longer needed
  - Smart repository management that preserves shared repositories
  - Improved CLI with subcommands for better organization

### Changed

### Fixed

### Removed


## [0.3.2] - 2025-03-09

### Added

### Changed

### Fixed

- Fixed handling of dead Sliver sessions:
  - Added validation to check if a Sliver session is in an invalid state
  - Improved error reporting for dead sessions with clear error messages
  - Prevented command execution on invalid sessions to avoid unexpected behavior

### Removed


## [0.3.1] - 2025-03-09

### Added

- Added support for custom .env file path:
  - Added `--env-file` command-line option to specify a custom .env file path
  - Default path is `$WISH_HOME/env`
  - Centralized settings management in `wish-models` package

### Changed

- Refactored settings management:
  - Moved settings from individual packages to `wish-models` package
  - All packages now use the same settings instance

### Fixed

- Fixed LangSmith integration:
  - Added automatic environment variable setup for LangChain/LangGraph tracing
  - Settings values are now properly passed to LangSmith via environment variables
- [wish-command-generation] Fixed a bug where the target machine environment from Sliver was not properly reflected in command generation

### Removed


## [0.3.0] - 2025-03-08

### Added

- Added system information collection capabilities for Sliver C2:
  - New model classes for system information (`SystemInfo`, `ExecutableInfo`, `ExecutableCollection`)
  - Factory classes for testing system information models
  - `SystemInfoCollector` for gathering OS information and executable files from remote systems
  - Integration with Sliver C2 backend to collect system information from compromised hosts
- Added OS-aware command generation:
  - Enhanced command generation to use system information for creating OS-specific commands
  - Updated prompts to include examples for different operating systems (Linux, Windows, macOS)
  - Improved user experience by generating commands that are compatible with the user's system

### Changed

### Fixed

### Removed


## [0.2.0] - 2025-03-08

### Added

- Added comprehensive documentation:
  - `docs/setup.md`: Installation and setup guide
  - `docs/usage-01-basic.md`: Basic usage guide
  - `docs/usage-02-knowledge-loader.md`: Knowledge loader usage guide
  - `docs/usage-03-C2.md`: Command and Control (C2) usage guide
- Added Sliver C2 integration:
  - New `SliverBackend` for executing commands on remote systems through Sliver C2
  - Command-line arguments `--sliver-config` and `--sliver-session` for connecting to Sliver C2
  - Automatic session detection when only one Sliver session is active

### Changed

### Fixed

### Removed


## [0.1.1] - 2025-03-08

### Added

- Added `wish-sh` command as an alternative to `wish` to avoid conflicts with macOS built-in Tcl/Tk `wish` command
- Added documentation for `wish-knowledge-loader` command in README

### Changed

### Fixed

### Removed


## [0.1.0] - 2025-03-08

### Added

- Initial release

### Changed

### Fixed

### Removed
